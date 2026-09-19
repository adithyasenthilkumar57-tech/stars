"""
ClearWay AI — Audio Alert Service
Siren detection pipeline: MFCC feature extraction → SVC classifier → TTS dispatch.
Labeled: SIMULATED audio monitoring. Not a real microphone integration.
"""
import io
import logging
import math
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np

from models.siren import (
    SirenDetectionEvent, PoliceAlertDispatch, SirenStatus,
    ApproachDirection, SirenEventRequest, JunctionMicrophoneStatus
)

logger = logging.getLogger(__name__)


class SirenClassifier:
    """
    Lightweight siren audio classifier.
    Uses MFCC features + scikit-learn SVC.
    Trained on synthetic siren/noise feature patterns (labeled SIMULATED).
    """

    def __init__(self):
        self._model = None
        self._ready = False
        self._init_model()

    def _init_model(self):
        try:
            from sklearn.svm import SVC
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline

            # Generate synthetic training data
            # Siren: high-frequency oscillation patterns → distinct MFCC signature
            rng = np.random.RandomState(42)
            n_samples = 400
            n_features = 40  # 40 MFCC coefficients

            # Siren-like patterns: structured harmonic content
            siren_X = np.zeros((n_samples // 2, n_features))
            for i in range(n_samples // 2):
                freq = random.uniform(0.5, 1.5)
                base = [math.sin(freq * j * 0.4) * (20 + j * 0.5) for j in range(n_features)]
                siren_X[i] = base + rng.randn(n_features) * 3.0

            # Background noise: random with lower structured content
            noise_X = rng.randn(n_samples // 2, n_features) * 10 + rng.uniform(-5, 5, n_features)

            X = np.vstack([siren_X, noise_X])
            y = [1] * (n_samples // 2) + [0] * (n_samples // 2)

            self._model = Pipeline([
                ('scaler', StandardScaler()),
                ('svc', SVC(kernel='rbf', probability=True, C=2.0, gamma='scale')),
            ])
            self._model.fit(X, y)
            self._ready = True
            logger.info("Siren classifier ready (SIMULATED — synthetic training data)")
        except ImportError:
            logger.warning("scikit-learn not available. Using heuristic siren detection.")
            self._ready = False

    def extract_mfcc(self, audio_buffer: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Extract 40 MFCC coefficients from audio buffer.
        If no real audio buffer, generates synthetic features for demo.
        """
        if audio_buffer is not None:
            try:
                import librosa
                mfccs = librosa.feature.mfcc(y=audio_buffer.astype(float), sr=22050, n_mfcc=40)
                return np.mean(mfccs, axis=1)
            except Exception as e:
                logger.warning(f"MFCC extraction failed: {e}")

        # Synthetic MFCC for demo/simulation
        features = np.array([
            math.sin(i * 0.4) * (20 + i * 0.5) + random.gauss(0, 2)
            for i in range(40)
        ])
        return features

    def classify(self, features: np.ndarray) -> Tuple[bool, float]:
        """Returns (is_siren, confidence)."""
        if not self._ready:
            # Heuristic: check if features have siren-like structure
            variance = float(np.var(features))
            oscillation = float(np.mean(np.abs(np.diff(features[:10]))))
            score = min(1.0, (oscillation / 15.0) * 0.6 + (variance / 200.0) * 0.4)
            return score > 0.75, score

        try:
            X = features.reshape(1, -1)
            proba = self._model.predict_proba(X)[0]
            confidence = float(proba[1])
            return confidence > 0.75, confidence
        except Exception as e:
            logger.warning(f"Classifier error: {e}")
            return False, 0.0


class TTSDispatcher:
    """
    Text-to-Speech voice alert dispatcher.
    Uses gTTS to generate MP3 voice alerts.
    Labeled: SIMULATED RADIO DISPATCH — not real police radio.
    """

    def __init__(self, audio_dir: str = "audio_alerts"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        self._gtts_available = self._check_gtts()

    def _check_gtts(self) -> bool:
        try:
            from gtts import gTTS
            return True
        except ImportError:
            logger.warning("gTTS not available. Voice alerts will be text-only.")
            return False

    def generate_alert_audio(
        self,
        junction_label: str,
        approach_direction: str,
        output_filename: str,
    ) -> Optional[str]:
        """
        Generate TTS voice alert audio file.
        Returns path to MP3 file or None if gTTS unavailable.
        """
        message = (
            f"Attention. Emergency vehicle approaching from {approach_direction} "
            f"at Junction {junction_label}. Clear the intersection immediately. "
            f"Repeat: Emergency vehicle approaching from {approach_direction} "
            f"at Junction {junction_label}. Clear the intersection."
        )

        if not self._gtts_available:
            return None

        try:
            from gtts import gTTS
            tts = gTTS(text=message, lang='en', slow=False)
            filepath = self.audio_dir / output_filename
            tts.save(str(filepath))
            logger.info(f"TTS audio generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    def get_message_text(self, junction_label: str, approach_direction: str) -> str:
        return (
            f"Attention — emergency vehicle approaching from {approach_direction.title()} "
            f"at Junction {junction_label}. Clear the intersection. "
            f"(Repeats 5 times — SIMULATED RADIO DISPATCH)"
        )


class AudioAlertService:
    """
    Continuous siren monitoring and alert dispatch service.
    All operations labeled SIMULATED unless real microphones connected.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.threshold = confidence_threshold
        self.classifier = SirenClassifier()
        self.tts = TTSDispatcher()
        self._active_events: Dict[str, SirenDetectionEvent] = {}
        self._active_dispatches: Dict[str, PoliceAlertDispatch] = {}
        self._event_history: List[SirenDetectionEvent] = []
        self._dispatch_history: List[PoliceAlertDispatch] = []

    def simulate_detection(
        self,
        junction_id: str,
        junction_label: str,
        force_detect: bool = False,
        data_source: str = "SIMULATED",
    ) -> Optional[SirenDetectionEvent]:
        """
        Simulate a siren detection cycle for a junction.
        Returns a SirenDetectionEvent if detection threshold exceeded.
        """
        features = self.classifier.extract_mfcc()
        if force_detect:
            # Inject siren-like signal
            features = np.array([
                math.sin(i * 0.4) * (25 + i * 0.6) + random.gauss(0, 1.5)
                for i in range(40)
            ])

        is_siren, confidence = self.classifier.classify(features)

        if not is_siren and not force_detect:
            return None

        if confidence < self.threshold and not force_detect:
            return None

        # Direction inference (simulated triangulation)
        directions = list(ApproachDirection)
        directions.remove(ApproachDirection.UNKNOWN)
        approach = random.choice(directions)
        dir_confidence = random.uniform(0.55, 0.82)

        event = SirenDetectionEvent(
            junction_id=junction_id,
            junction_label=junction_label,
            detected_at=datetime.utcnow(),
            confidence=round(confidence, 3),
            mfcc_features=features.tolist(),
            approach_direction=approach,
            direction_estimate_method="SIMULATED_TRIANGULATION",
            direction_confidence=round(dir_confidence, 3),
            status=SirenStatus.DETECTED,
            is_active=True,
            data_source=data_source,
        )

        self._active_events[junction_id] = event
        self._event_history.append(event)
        logger.info(f"Siren detected at {junction_label}: confidence={confidence:.3f}, direction={approach.value}")

        return event

    def process_event_request(self, req: SirenEventRequest) -> SirenDetectionEvent:
        """Process an explicit siren event (from API or audio_alert_service)."""
        event = SirenDetectionEvent(
            junction_id=req.junction_id,
            junction_label=req.junction_label,
            detected_at=datetime.utcnow(),
            confidence=req.confidence,
            approach_direction=req.approach_direction,
            direction_estimate_method="SIMULATED_TRIANGULATION",
            direction_confidence=round(random.uniform(0.55, 0.82), 3),
            status=SirenStatus.DETECTED,
            is_active=True,
            data_source=req.data_source,
        )
        self._active_events[req.junction_id] = event
        self._event_history.append(event)
        return event

    def dispatch_police_alert(
        self, event: SirenDetectionEvent, officer_id: Optional[str] = None
    ) -> PoliceAlertDispatch:
        """
        Dispatch police voice alert.
        Generates TTS audio and logs dispatch.
        Labeled: SIMULATED RADIO DISPATCH.
        """
        message = self.tts.get_message_text(
            event.junction_label, event.approach_direction.value
        )
        audio_filename = f"alert_{event.junction_label}_{int(time.time())}.mp3"
        audio_path = self.tts.generate_alert_audio(
            event.junction_label, event.approach_direction.value, audio_filename
        )

        dispatch = PoliceAlertDispatch(
            siren_event_id=event.id,
            junction_id=event.junction_id,
            junction_label=event.junction_label,
            officer_id=officer_id,
            voice_message_text=message,
            voice_audio_url=f"/audio/{audio_filename}" if audio_path else None,
            repeat_count=5,
            dispatched_at=datetime.utcnow(),
            officer_status=SirenStatus.ALERT_DISPATCHED,
            approach_direction=event.approach_direction,
            dispatch_method="SIMULATED_RADIO_DISPATCH",
        )

        self._active_dispatches[event.junction_id] = dispatch
        self._dispatch_history.append(dispatch)

        # Update event status
        event.status = SirenStatus.ALERT_DISPATCHED
        if event.junction_id in self._active_events:
            self._active_events[event.junction_id].status = SirenStatus.ALERT_DISPATCHED

        logger.info(f"Police alert dispatched for {event.junction_label} (×{dispatch.repeat_count})")
        return dispatch

    def acknowledge(self, junction_id: str, status: SirenStatus, officer_id: Optional[str] = None) -> Optional[PoliceAlertDispatch]:
        """Update officer acknowledgment status."""
        dispatch = self._active_dispatches.get(junction_id)
        if dispatch is None:
            return None

        dispatch.officer_status = status
        if status == SirenStatus.OFFICER_ACKNOWLEDGED:
            dispatch.acknowledged_at = datetime.utcnow()
            dispatch.officer_id = officer_id
        elif status == SirenStatus.CLEARANCE_IN_PROGRESS:
            dispatch.clearance_started_at = datetime.utcnow()
        elif status in [SirenStatus.PATH_CLEAR, SirenStatus.COMPLETE]:
            dispatch.path_cleared_at = datetime.utcnow()
            # Mark as complete
            if junction_id in self._active_events:
                self._active_events[junction_id].is_active = False
                self._active_events[junction_id].status = SirenStatus.COMPLETE
            del self._active_dispatches[junction_id]
            self._active_events.pop(junction_id, None)

        elif status == SirenStatus.FALSE_POSITIVE:
            if junction_id in self._active_events:
                self._active_events[junction_id].status = SirenStatus.FALSE_POSITIVE
                self._active_events[junction_id].is_active = False
            self._active_dispatches.pop(junction_id, None)
            self._active_events.pop(junction_id, None)

        return dispatch

    def get_junction_status(self, junction_id: str, junction_label: str) -> JunctionMicrophoneStatus:
        event = self._active_events.get(junction_id)
        dispatch = self._active_dispatches.get(junction_id)
        status = SirenStatus.MONITORING
        if event:
            status = event.status
        return JunctionMicrophoneStatus(
            junction_id=junction_id,
            junction_label=junction_label,
            microphone_online=True,
            monitoring_active=True,
            last_detection_at=event.detected_at if event else None,
            current_confidence=event.confidence if event else 0.0,
            active_event=event,
            active_dispatch=dispatch,
            status=status,
            data_source="SIMULATED",
        )

    def get_all_events(self) -> List[SirenDetectionEvent]:
        return self._event_history[-50:]  # Last 50

    def get_all_dispatches(self) -> List[PoliceAlertDispatch]:
        return self._dispatch_history[-50:]

    def get_active_events(self) -> Dict[str, SirenDetectionEvent]:
        return self._active_events.copy()

    def get_audio_file_path(self, filename: str) -> Optional[str]:
        path = Path("audio_alerts") / filename
        return str(path) if path.exists() else None


# Singleton
audio_alert_service = AudioAlertService()
