"""Optional GPU adapter. No model import or download during deterministic tests."""

from importlib.metadata import version
from typing import Protocol, runtime_checkable

MODEL = "Qwen/Qwen3-8B-AWQ"
GENERATION = {
    "do_sample": False,
    "num_beams": 1,
    "max_new_tokens": 2048,
    "temperature": None,
    "top_p": None,
    "top_k": None,
}
VERSIONS = {"transformers": "4.51.3", "accelerate": "1.10.1", "autoawq": "0.2.9"}


@runtime_checkable
class Backend(Protocol):
    """Structural interface for any Stage-B model backend.

    StageBPipeline depends on this interface. QwenBackend is the canonical
    benchmark implementation. StubBackend provides a development-only
    alternative for machines that cannot satisfy QwenBackend's GPU requirements.
    """

    model: str
    revision: str
    quantization: str

    def generate(self, system: str, user: str) -> dict: ...

    def peak_vram(self) -> int | None: ...


class StubBackend:
    """Development-only backend for pipeline testing without GPU inference.

    Returns a fixed unsupported verdict for every query. NOT valid for
    benchmark evaluation — results will be recorded as contract failures
    because the canned response cannot match arbitrary claim structures.
    """

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
            "Benchmark CUDA PyTorch is not installed; use the isolated Colab workflow"
        ) from e
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; model not loaded")
    free, total = torch.cuda.mem_get_info()
    if total < 14 * 1024**3 or free < 12 * 1024**3:
        raise RuntimeError(
            f"Need >=14 GiB total / >=12 GiB free; found {total / 1024**3:.2f}/{free / 1024**3:.2f} GiB"
        )
    actual = {name: version(name) for name in VERSIONS}
    if actual != VERSIONS:
        raise RuntimeError(f"Benchmark package mismatch: {actual}; expected {VERSIONS}")
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
            raise ValueError("Use immutable Hugging Face commit SHA as model revision")
        self.hardware = preflight()
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig

        torch.manual_seed(42)
        self.revision = revision
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=revision)
        self.network = AutoModelForCausalLM.from_pretrained(
            MODEL,
            revision=revision,
            torch_dtype=torch.float16,
            device_map={"": 0},
            attn_implementation="eager",
        )
        quant = self.network.config.quantization_config
        if quant.get("quant_method") != "awq" or quant.get("bits") != 4:
            raise RuntimeError("Loaded checkpoint does not declare AWQ 4-bit")
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
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(text, return_tensors="pt", truncation=False).to("cuda")
        n = inputs.input_ids.shape[-1]
        if n + GENERATION["max_new_tokens"] > min(
            32768, self.network.config.max_position_embeddings
        ):
            raise RuntimeError(
                "Full evidence packet exceeds context; refusing silent truncation"
            )
        with torch.inference_mode():
            output = self.network.generate(**inputs, generation_config=self.config)
        tokens = output[0, n:]
        return {
            "text": self.tokenizer.decode(tokens, skip_special_tokens=True),
            "input_tokens": n,
            "output_tokens": len(tokens),
        }

    def peak_vram(self):
        import torch

        return torch.cuda.max_memory_allocated()
