---
title: MedicalPlab API
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# MedicalPlab Clinical Intelligence Platform - Hugging Face Spaces Backend

This repository powers the cloud backend API for **MedicalPlab** ([https://medical-plab.vercel.app](https://medical-plab.vercel.app)).

## Features
- Evidence-grounded Socratic tutor chat (`/ai/chat`)
- Clinical safety interdiction gate (NICE CG127, NG185)
- Bayesian Knowledge Tracing student analytics (`/student/analytics`, `/student/attempts`)
- Continuous health monitoring (`/health`)

## Quick Deployment to Hugging Face Spaces (No Credit Card Required)
1. Create a Space on Hugging Face: [https://huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Docker** SDK (Blank).
3. Name your space `medicalplab-api`.
4. Push this repository or sync via GitHub:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/medicalplab-api
   git push space main
   ```
5. Your public HTTPS API will be live at:
   `https://<your-username>-medicalplab-api.hf.space`
6. Set `NEXT_PUBLIC_API_URL` on Vercel to `https://<your-username>-medicalplab-api.hf.space`.
