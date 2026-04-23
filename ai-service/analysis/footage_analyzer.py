"""
CCTV Footage Analyzer
Processes recorded CCTV footage, detects risk events, outputs highlight reel + summary
"""

import cv2
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class FootageAnalyzer:
    """
    Analyzes recorded CCTV footage for risk events.
    Produces:
      - A highlight video containing only risky segments
      - A text summary of all detected events
    """

    def __init__(self, config, person_detector, zone_analyzer,
                 loitering_detector, unattended_object_detector, risk_engine):
        self.config = config
        self.person_detector = person_detector
        self.zone_analyzer = zone_analyzer
        self.loitering_detector = loitering_detector
        self.unattended_object_detector = unattended_object_detector
        self.risk_engine = risk_engine

        # How many seconds of buffer to include around a risk event
        self.pre_event_buffer_sec = getattr(config, 'CLIP_PRE_BUFFER_SEC', 3)
        self.post_event_buffer_sec = getattr(config, 'CLIP_POST_BUFFER_SEC', 3)

        # Minimum risk score to consider a frame "risky"
        self.risk_threshold = getattr(config, 'FOOTAGE_RISK_THRESHOLD', 1)

    # Public API
    def analyze(
        self,
        input_video_path: str,
        output_video_path: str,
        summary_path: str,
        restricted_zones: List[Dict] = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Main entry point. Analyze a recorded video file.

        Args:
            input_video_path:  Path to the source CCTV footage.
            output_video_path: Where to write the highlight reel.
            summary_path:      Where to write the text summary.
            restricted_zones:  Optional list of zone dicts (same format as live mode).
            progress_callback: Optional callable(percent: float) for progress updates.

        Returns:
            dict with keys: total_frames, processed_frames, events, risk_segments,
                            output_video, summary_file, duration_seconds
        """
        restricted_zones = restricted_zones or []

        # Reset detectors so footage analysis is independent of live state
        self.loitering_detector.reset()
        self.unattended_object_detector.reset()
        self.risk_engine.reset()

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {input_video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps

        logger.info(f"Footage: {input_video_path} | {total_frames} frames | {fps:.1f} fps | {duration_sec:.1f}s")

        # ---- Pass 1: scan every frame, record risk scores + events ----
        frame_risk_scores: List[float] = []   # one score per frame
        all_events: List[Dict]         = []
        frame_events: List[List[Dict]] = []   # events per frame

        frame_idx = 0
        video_start = datetime(2000, 1, 1)  # synthetic base timestamp

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = video_start + timedelta(seconds=frame_idx / fps)

            # Run detection pipeline
            persons     = self.person_detector.detect(frame)
            suspicious  = [p for p in persons if not p.get('is_whitelisted', False)]

            zone_events      = self.zone_analyzer.check_intrusions(suspicious, restricted_zones, timestamp)
            loiter_events    = self.loitering_detector.detect(suspicious, timestamp)
            unattended_events = self.unattended_object_detector.detect(frame, persons, timestamp)

            frame_ev = zone_events + loiter_events + unattended_events
            risk_score, _ = self.risk_engine.calculate_risk(frame_ev)

            frame_risk_scores.append(risk_score)
            frame_events.append(frame_ev)

            # Stamp frame number + video timestamp onto each event
            for ev in frame_ev:
                ev['frame']          = frame_idx
                ev['video_timestamp'] = self._seconds_to_hhmmss(frame_idx / fps)
                all_events.append(ev)

            frame_idx += 1

            if progress_callback and frame_idx % 30 == 0:
                progress_callback(min(frame_idx / total_frames * 80, 80))  # first 80 % = scan

        cap.release()

        # ---- Identify risky segments (merge close intervals) ----
        risky_frames = [i for i, s in enumerate(frame_risk_scores) if s >= self.risk_threshold]
        segments = self._merge_segments(risky_frames, fps,
                                        self.pre_event_buffer_sec,
                                        self.post_event_buffer_sec,
                                        total_frames)

        # ---- Pass 2: write highlight reel ----
        self._write_highlight_video(
            input_video_path, output_video_path,
            segments, fps, width, height,
            frame_risk_scores, frame_events
        )

        if progress_callback:
            progress_callback(95)

        # ---- Write summary text ----
        summary_stats = self._write_summary(
            summary_path, input_video_path, all_events,
            segments, fps, duration_sec, total_frames
        )

        if progress_callback:
            progress_callback(100)

        return {
            'total_frames':     total_frames,
            'processed_frames': frame_idx,
            'duration_seconds': duration_sec,
            'events':           all_events,
            'risk_segments':    segments,
            'output_video':     output_video_path,
            'summary_file':     summary_path,
            'stats':            summary_stats,
        }

    # Internal helpers
    def _merge_segments(
        self,
        risky_frames: List[int],
        fps: float,
        pre_buf: float,
        post_buf: float,
        total_frames: int
    ) -> List[Tuple[int, int]]:
        """Merge nearby risky frames into continuous segments with buffer."""
        if not risky_frames:
            return []

        pre_frames  = int(pre_buf  * fps)
        post_frames = int(post_buf * fps)
        gap_frames  = int(fps * 2)   # merge if gap < 2 s

        segments = []
        seg_start = risky_frames[0]
        seg_end   = risky_frames[0]

        for f in risky_frames[1:]:
            if f - seg_end <= gap_frames:
                seg_end = f
            else:
                segments.append((seg_start, seg_end))
                seg_start = f
                seg_end   = f
        segments.append((seg_start, seg_end))

        # Apply buffer and clamp to valid range
        buffered = []
        for s, e in segments:
            buffered.append((
                max(0, s - pre_frames),
                min(total_frames - 1, e + post_frames)
            ))

        # Merge overlapping buffered segments
        merged = [buffered[0]]
        for s, e in buffered[1:]:
            if s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))

        return merged

    def _write_highlight_video(
        self,
        input_path: str,
        output_path: str,
        segments: List[Tuple[int, int]],
        fps: float,
        width: int,
        height: int,
        frame_risk_scores: List[float],
        frame_events: List[List[Dict]]
    ):
        """Write only the risky segments to the output video with overlays."""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not segments:
            logger.info("No risky segments found; output video will be empty.")
            out.release()
            return

        cap = cv2.VideoCapture(input_path)

        for seg_start, seg_end in segments:
            cap.set(cv2.CAP_PROP_POS_FRAMES, seg_start)
            for fi in range(seg_start, seg_end + 1):
                ret, frame = cap.read()
                if not ret:
                    break

                risk_score = frame_risk_scores[fi] if fi < len(frame_risk_scores) else 0
                events     = frame_events[fi]        if fi < len(frame_events)      else []

                frame = self._draw_overlay(frame, fi, fps, risk_score, events)
                out.write(frame)

        cap.release()
        out.release()
        logger.info(f"Highlight video written: {output_path}")

    def _draw_overlay(
        self,
        frame: np.ndarray,
        frame_idx: int,
        fps: float,
        risk_score: float,
        events: List[Dict]
    ) -> np.ndarray:
        """Draw HUD overlay: timestamp, risk badge, event labels."""
        h, w = frame.shape[:2]
        overlay = frame.copy()

        # Semi-transparent top bar
        cv2.rectangle(overlay, (0, 0), (w, 45), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        # Timestamp
        ts = self._seconds_to_hhmmss(frame_idx / fps)
        cv2.putText(frame, f"TIME {ts}", (10, 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (200, 200, 200), 1, cv2.LINE_AA)

        # Risk badge
        if risk_score >= self.risk_threshold:
            level = self._score_to_level(risk_score)
            color = {'LOW': (0,200,80), 'MEDIUM': (0,165,255), 'HIGH': (0,0,220)}.get(level, (100,100,100))
            label = f"RISK: {level} ({int(risk_score)})"
            (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.7, 1)
            cv2.rectangle(frame, (w - tw - 20, 5), (w - 5, 40), color, -1)
            cv2.putText(frame, label, (w - tw - 15, 30),
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA)

        # Event type labels (bottom strip)
        if events:
            unique_types = list({e['type'] for e in events})
            for i, etype in enumerate(unique_types):
                cv2.putText(frame, f"⚠ {etype}", (10, h - 15 - i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 80, 255), 2, cv2.LINE_AA)

        return frame

    def _write_summary(
        self,
        summary_path: str,
        input_path: str,
        all_events: List[Dict],
        segments: List[Tuple[int, int]],
        fps: float,
        duration_sec: float,
        total_frames: int
    ) -> Dict:
        """Write a human-readable text summary to disk."""
        os.makedirs(os.path.dirname(summary_path) or '.', exist_ok=True)

        # Aggregate stats
        type_counts: Dict[str, int] = {}
        for ev in all_events:
            type_counts[ev['type']] = type_counts.get(ev['type'], 0) + 1

        total_risk_duration = sum(
            (e - s) / fps for s, e in segments
        )

        lines = []
        lines.append("=" * 70)
        lines.append("       AI SURVEILLANCE CO-PILOT — FOOTAGE ANALYSIS SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Generated     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Source file   : {os.path.basename(input_path)}")
        lines.append(f"Footage length: {self._seconds_to_hhmmss(duration_sec)}  ({total_frames} frames @ {fps:.1f} fps)")
        lines.append(f"Risk segments : {len(segments)}  ({self._seconds_to_hhmmss(total_risk_duration)} total risk footage)")
        lines.append("")

        lines.append("─" * 70)
        lines.append("EVENT SUMMARY")
        lines.append("─" * 70)
        if not all_events:
            lines.append("  No risk events detected. Footage appears safe.")
        else:
            for etype, count in sorted(type_counts.items()):
                lines.append(f"  {etype:<30} {count:>4} occurrence(s)")
        lines.append("")

        lines.append("─" * 70)
        lines.append("RISK SEGMENTS (clips included in output video)")
        lines.append("─" * 70)
        if not segments:
            lines.append("  None.")
        else:
            for idx, (s, e) in enumerate(segments, 1):
                start_ts = self._seconds_to_hhmmss(s / fps)
                end_ts   = self._seconds_to_hhmmss(e / fps)
                dur      = (e - s) / fps
                lines.append(f"  Segment {idx:>2}: {start_ts} → {end_ts}  ({dur:.1f}s)")
        lines.append("")

        lines.append("─" * 70)
        lines.append("DETAILED EVENT LOG")
        lines.append("─" * 70)
        if not all_events:
            lines.append("  No events to log.")
        else:
            for ev in all_events:
                ts    = ev.get('video_timestamp', '??:??:??')
                etype = ev.get('type', 'UNKNOWN')
                msg   = ev.get('details', {}).get('message', '')
                pid   = ev.get('person_id', '')
                oid   = ev.get('object_id', '')
                zname = ev.get('zone_name', '')

                subject = f"Person {pid}" if pid else f"Object {oid}" if oid else "Unknown"
                zone_str = f" | Zone: {zname}" if zname else ""
                lines.append(f"  [{ts}]  {etype:<25} {subject}{zone_str}")
                if msg:
                    lines.append(f"            {msg}")
        lines.append("")
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        text = "\n".join(lines)
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(text)

        logger.info(f"Summary written: {summary_path}")
        return {
            'event_counts':          type_counts,
            'risk_segment_count':    len(segments),
            'total_risk_seconds':    round(total_risk_duration, 1),
            'total_events':          len(all_events),
        }

    # Utilities
    @staticmethod
    def _seconds_to_hhmmss(seconds: float) -> str:
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def _score_to_level(score: float) -> str:
        if score <= 4:
            return 'LOW'
        if score <= 8:
            return 'MEDIUM'
        return 'HIGH'