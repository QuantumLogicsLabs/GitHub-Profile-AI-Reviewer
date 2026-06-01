from __future__ import annotations

from dataclasses import dataclass

try:
    import torch
    import torch.nn as nn
except Exception:
    torch = None
    nn = None


if nn is not None:
    class DeveloperScoringModel(nn.Module):
        def __init__(self, input_dim: int = 768) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 256),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(256, 128),
                nn.ReLU(),
            )
            self.level_head = nn.Linear(128, 4)
            self.hiring_head = nn.Linear(128, 1)

        def forward(self, x):
            feat = self.encoder(x)
            level_logits = self.level_head(feat)
            hiring = torch.sigmoid(self.hiring_head(feat)) * 100
            return level_logits, hiring
else:
    class DeveloperScoringModel:  # type: ignore[no-redef]
        def __init__(self, input_dim: int = 768) -> None:
            self.input_dim = input_dim


@dataclass
class ScoreOutput:
    level: str
    confidence: float
    hiring_score: int


class ScoringEngine:
    LEVELS = ["Junior", "Mid", "Senior", "Staff / Principal"]

    def __init__(self, input_dim: int = 768) -> None:
        self._model = DeveloperScoringModel(input_dim=input_dim)

    def infer(self, embedding: list[float], activity_score: float, consistency_score: float) -> ScoreOutput:
        if torch is None or nn is None or not isinstance(self._model, nn.Module):
            return self._heuristic(activity_score, consistency_score)

        x = torch.tensor([embedding], dtype=torch.float32)
        self._model.eval()
        with torch.no_grad():
            level_logits, hiring = self._model(x)

        probs = torch.softmax(level_logits[0], dim=-1)
        level_idx = int(torch.argmax(probs).item())
        base_hiring = int(round(float(hiring[0].item())))
        blended_hiring = int(max(0, min(100, 0.6 * base_hiring + 0.4 * activity_score)))
        confidence = float(probs[level_idx].item())
        return ScoreOutput(level=self.LEVELS[level_idx], confidence=round(confidence, 2), hiring_score=blended_hiring)

    def _heuristic(self, activity_score: float, consistency_score: float) -> ScoreOutput:
        hiring = int(max(0, min(100, round(0.7 * activity_score + 0.3 * consistency_score))))
        if hiring >= 90:
            return ScoreOutput("Staff / Principal", 0.95, hiring)
        if hiring >= 75:
            return ScoreOutput("Senior", 0.90, hiring)
        if hiring >= 55:
            return ScoreOutput("Mid", 0.86, hiring)
        return ScoreOutput("Junior", 0.82, hiring)
