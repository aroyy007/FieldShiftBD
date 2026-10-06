import json
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

from PIL import Image

from app.core.config import settings


MODEL_ID = "Saon110/bd-crop-vegetable-plant-disease-model"
DEFAULT_WEIGHTS_PATH = Path(__file__).resolve().parents[2] / "model" / "crop_veg_plant_disease_model.pth"
CLASS_MAPPING_PATH = Path(__file__).resolve().parents[1] / "data" / "plant_disease_classes.json"


@dataclass(frozen=True)
class DiseasePrediction:
    label: str
    score: float


class DiseasePredictor(Protocol):
    def predict(self, image: Image.Image) -> DiseasePrediction:
        ...


class InferenceUnavailableError(RuntimeError):
    """Raised when the configured model cannot be loaded or run."""


class TorchDiseasePredictor:
    """Lazy, single-process ResNet50 inference adapter for the downloaded weights."""

    def __init__(self, weights_path: str | Path | None = None):
        configured_path = weights_path or settings.DISEASE_MODEL_WEIGHTS_PATH
        self.weights_path = Path(configured_path) if configured_path else DEFAULT_WEIGHTS_PATH
        self._runtime: tuple[Any, Any, Any, list[str], Any] | None = None
        self._load_lock = threading.Lock()

    def predict(self, image: Image.Image) -> DiseasePrediction:
        torch, model, transform, labels, device = self._ensure_loaded()
        tensor = transform(image).unsqueeze(0).to(device)
        with torch.inference_mode():
            probabilities = model(tensor).softmax(dim=1)
            score, index = probabilities[0].max(dim=0)
        return DiseasePrediction(label=labels[int(index.item())], score=float(score.item()))

    def _ensure_loaded(self) -> tuple[Any, Any, Any, list[str], Any]:
        if self._runtime is not None:
            return self._runtime

        with self._load_lock:
            if self._runtime is not None:
                return self._runtime

            try:
                import torch
                from torchvision import models, transforms

                if not self.weights_path.is_file():
                    raise InferenceUnavailableError(
                        "Disease model weights are missing. Place the downloaded checkpoint at "
                        "backend/model/crop_veg_plant_disease_model.pth or set "
                        "DISEASE_MODEL_WEIGHTS_PATH."
                    )

                with CLASS_MAPPING_PATH.open("r", encoding="utf-8") as mapping_file:
                    mapping = json.load(mapping_file)
                if len(mapping) != 94 or any(str(index) not in mapping for index in range(94)):
                    raise ValueError("The model class mapping must contain exactly 94 indexed labels")
                labels = [mapping[str(index)] for index in range(94)]

                device = torch.device("cpu")
                if torch.cuda.is_available():
                    device = torch.device("cuda")
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = torch.device("mps")

                model = models.resnet50(weights=None)
                model.fc = torch.nn.Sequential(
                    torch.nn.Linear(model.fc.in_features, 512),
                    torch.nn.ReLU(),
                    torch.nn.Dropout(0.2),
                    torch.nn.Linear(512, 94),
                )

                checkpoint = torch.load(
                    self.weights_path,
                    map_location="cpu",
                    weights_only=True,
                )
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    state_dict = checkpoint["model_state_dict"]
                elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                else:
                    state_dict = checkpoint
                if not isinstance(state_dict, dict):
                    raise ValueError("The checkpoint does not contain a model state dictionary")
                if any(key.startswith("module.") for key in state_dict):
                    state_dict = {
                        key.removeprefix("module."): value
                        for key, value in state_dict.items()
                    }

                model.load_state_dict(state_dict, strict=True)
                model.to(device)
                model.eval()
                transform = transforms.Compose(
                    [
                        transforms.Resize(256),
                        transforms.CenterCrop(224),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225],
                        ),
                    ]
                )
                self._runtime = (torch, model, transform, labels, device)
                return self._runtime
            except InferenceUnavailableError:
                raise
            except Exception as error:
                raise InferenceUnavailableError(
                    "The crop disease model could not be loaded. Check the model files and ML dependencies."
                ) from error


@lru_cache(maxsize=1)
def get_torch_disease_predictor() -> TorchDiseasePredictor:
    return TorchDiseasePredictor()


def get_disease_predictor() -> DiseasePredictor:
    return get_torch_disease_predictor()
