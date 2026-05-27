import asyncio
from typing import TYPE_CHECKING

import open_clip
import torch
import torchvision.models as tv_models
import torchvision.transforms as T
from nudenet import NudeClassifier

if TYPE_CHECKING:
    from fastapi import FastAPI


async def load_models(app: "FastAPI") -> None:
    """Load all ML models into app.state. Runs once at startup via lifespan."""

    def _load_sync():
        # ── CLIP ViT-B/32 ──────────────────────────────────────────────────────
        clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="openai"
        )
        clip_model.eval()
        clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")

        # ── MobileNetV3-Large (ImageNet classifier) ────────────────────────────
        weights = tv_models.MobileNet_V3_Large_Weights.DEFAULT
        mobilenet = tv_models.mobilenet_v3_large(weights=weights)
        mobilenet.eval()
        mobilenet_preprocess = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        imagenet_labels = weights.meta["categories"]

        # ── NudeNet classifier (ONNX-backed) ───────────────────────────────────
        nude_classifier = NudeClassifier()

        return (
            clip_model, clip_preprocess, clip_tokenizer,
            mobilenet, mobilenet_preprocess, imagenet_labels,
            nude_classifier,
        )

    (
        app.state.clip_model,
        app.state.clip_preprocess,
        app.state.clip_tokenizer,
        app.state.mobilenet,
        app.state.mobilenet_preprocess,
        app.state.imagenet_labels,
        app.state.nude_classifier,
    ) = await asyncio.to_thread(_load_sync)

    app.state.models_loaded = True


def get_clip(app):
    return app.state.clip_model, app.state.clip_preprocess, app.state.clip_tokenizer


def get_mobilenet(app):
    return app.state.mobilenet, app.state.mobilenet_preprocess, app.state.imagenet_labels


def get_nudenet(app):
    return app.state.nude_classifier
