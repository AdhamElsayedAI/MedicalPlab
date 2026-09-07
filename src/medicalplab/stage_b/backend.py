"""Optional GPU adapters.

No model import or download during deterministic tests.

Contains:
- QwenBackend: canonical benchmark backend.
- LocalQwenBackend: local development backend.
- StubBackend: deterministic test backend.
"""

from importlib.metadata import version, PackageNotFoundError
from typing import Protocol, runtime_checkable
import warnings


# ---------------------------------------------------------------------------
# Canonical benchmark backend
# ---------------------------------------------------------------------------

MODEL = "Qwen/Qwen3-8B-AWQ"

GENERATION = {
    "do_sample": False,
    "num_beams": 1,
    "max_new_tokens": 2048,
}

VERSIONS = {
    "transformers": "4.51.3",
    "accelerate": "1.10.1",
    "autoawq": "0.2.9",
}


@runtime_checkable
class Backend(Protocol):
    model: str
    revision: str
    quantization: str

    def generate(self, system: str, user: str) -> dict:
        ...

    def peak_vram(self) -> int | None:
        ...


class StubBackend:
    model = "stub"
    revision = "local-development"
    quantization = "none"

    def generate(self, system, user):
        return {
            "text": '{"claims":[]}',
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def peak_vram(self):
        return None



def preflight():
    try:
        import torch
    except ImportError as e:
        raise RuntimeError(
            "Benchmark CUDA PyTorch is not installed"
        ) from e

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required")

    free, total = torch.cuda.mem_get_info()

    if total < 4 * 1024**3:
        raise RuntimeError(
            f"Need >=4 GiB VRAM, found {total/1024**3:.2f} GiB"
        )

    actual = {}

    for name in VERSIONS:
        try:
            actual[name] = version(name)
        except PackageNotFoundError:
            actual[name] = None

    missing = {
        k: v for k, v in actual.items()
        if v is None
    }

    if missing:
        raise RuntimeError(
            f"Missing benchmark packages: {missing}"
        )

    if actual != VERSIONS:
        raise RuntimeError(
            f"Benchmark package mismatch: {actual}"
        )

    return {
        "gpu": torch.cuda.get_device_name(),
        "total_vram": total,
        "free_vram": free,
        "packages": actual,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
    }



class QwenBackend:

    model = MODEL
    quantization = "AWQ 4-bit"

    def __init__(self, revision):

        import re

        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(
                "Use immutable HuggingFace commit SHA"
            )

        self.hardware = preflight()

        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            GenerationConfig,
        )

        torch.manual_seed(42)

        self.revision = revision

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL,
            revision=revision
        )

        self.network = AutoModelForCausalLM.from_pretrained(
            MODEL,
            revision=revision,
            torch_dtype=torch.float16,
            device_map="auto",
            max_memory={
                0: "5GiB",
                "cpu": "8GiB",
            },
            attn_implementation="eager",
        )

        quant = self.network.config.quantization_config

        if (
            quant.get("quant_method") != "awq"
            or quant.get("bits") != 4
        ):
            raise RuntimeError(
                "Loaded checkpoint is not AWQ 4-bit"
            )

        self.network.eval()

        self.config = GenerationConfig(
            **GENERATION,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )

        torch.cuda.reset_peak_memory_stats()



    def generate(self, system, user):

        import torch

        text = self.tokenizer.apply_chat_template(
            [
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": user
                },
            ],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=False,
        ).to("cuda")

        with torch.inference_mode():

            output = self.network.generate(
                **inputs,
                generation_config=self.config
            )

        tokens = output[0, inputs.input_ids.shape[-1]:]

        return {
            "text": self.tokenizer.decode(
                tokens,
                skip_special_tokens=True
            ),
            "input_tokens": inputs.input_ids.shape[-1],
            "output_tokens": len(tokens),
        }



    def peak_vram(self):

        import torch

        return torch.cuda.max_memory_allocated()



# ---------------------------------------------------------------------------
# Local RTX3060 development backend
# ---------------------------------------------------------------------------

LOCAL_MODEL = "Qwen/Qwen3-4B"

LOCAL_GENERATION = {
    "do_sample": False,
    "num_beams": 1,
    "max_new_tokens": 1024,
}


def local_preflight():
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required")

    free, total = torch.cuda.mem_get_info()

    if total < 6 * 1024**3:
        warnings.warn(
            "GPU has less than recommended 6GB VRAM"
        )

    return {
        "gpu": torch.cuda.get_device_name(),
        "total_vram": total,
        "free_vram": free,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
    }


class LocalQwenBackend:

    model = LOCAL_MODEL
    quantization = "BNB NF4"

    def __init__(self, revision="main"):

        self.hardware = local_preflight()

        import torch

        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            BitsAndBytesConfig,
        )

        torch.manual_seed(42)

        self.revision = revision

        self.tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_MODEL,
            revision=revision
        )

        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )

        self.network = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL,
            revision=revision,
            device_map="auto",
            torch_dtype=torch.float16,
            quantization_config=quant_config,
            low_cpu_mem_usage=True,
        )

        self.network.eval()

        # Normalize model-level generation_config to greedy decoding.
        # Qwen3 ships with do_sample=True, top_p=0.95, temperature=0
        # in its saved generation_config.json.
        #
        # We write None directly into gc.__dict__ to shadow the class-level
        # descriptor without triggering setter validation. delattr is avoided
        # because it exposes the class descriptor which returns a non-None
        # default that Transformers' merge path then picks up and rejects.
        gc = self.network.generation_config
        gc.__dict__["do_sample"] = False
        gc.__dict__["temperature"] = None
        gc.__dict__["top_p"] = None
        gc.__dict__["top_k"] = None

        self._eos_token_id = self.tokenizer.eos_token_id
        self._pad_token_id = self.tokenizer.pad_token_id

        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()


    def generate(self, system, user):

        import torch

        prompt = self.tokenizer.apply_chat_template(
            [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt"
        ).to("cuda")


        with torch.inference_mode():

            output = self.network.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=LOCAL_GENERATION["max_new_tokens"],
                eos_token_id=self._eos_token_id,
                pad_token_id=self._pad_token_id,
            )


        tokens = output[0, inputs.input_ids.shape[-1]:]

        return {
            "text": self.tokenizer.decode(
                tokens,
                skip_special_tokens=True
            ),
            "input_tokens": inputs.input_ids.shape[-1],
            "output_tokens": len(tokens),
        }


    def peak_vram(self):

        import torch

        return torch.cuda.max_memory_allocated()