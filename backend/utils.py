import json
import re
from typing import Dict, List, Iterable, Union


class ParserUtil:

    @staticmethod
    def parse_ndjson_content(content: Union[bytes, str]) -> List[Dict]:
        """
        Reads an NDJSON file and returns a list of normalized records.
        """
        text = content.decode("utf-8", errors="ignore") if isinstance(content, (bytes, bytearray)) else content
        normalized: List[Dict] = []
        for i, line in enumerate(text.splitlines()):  # handles \n, \r\n, trailing newline
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if not isinstance(rec, dict):
                    continue
            except json.JSONDecodeError:
                continue

            norm = ParserUtil._normalize_record(rec)
            norm["_idx"] = i
            normalized.append(norm)

        return normalized

    @staticmethod
    def _normalize_record(rec: Dict) -> Dict:
        """
        Convert one OTel-style record into target schema.
        """
        ra = rec.get("resource_attributes") or {}
        attrs = rec.get("attributes") or {}
        scope = rec.get("instrumentation_scope") or {}

        return {
            "clusterUid": str(ra.get("k8s.cluster.uid", "")),
            "containerId": str(ra.get("container.id") or ra.get("k8s.pod.uid") or ""),
            "containerName": str(
                ra.get("k8s.container.name")
                or ra.get("service.name")
                or ra.get("k8s.deployment.name")
                or scope.get("name")
                or "unknown"
            ),
            "log": str(rec.get("body", "")),
            "namespace": str(ra.get("k8s.namespace.name") or ra.get("service.namespace") or "default"),
            "podName": str(ra.get("k8s.pod.name") or ""),
            "stream": str(attrs.get("log.iostream") or "stdout"),
            "timestamp": str(rec.get("timestamp", "")),
        }


class LogFilter:
    STOP_WORDS = {
        "a", "an", "the", "and", "or", "for", "with",
        "on", "at", "by", "in", "to", "of", "service", "is", "are",
        "log", "logs"
    }

    @staticmethod
    def extract_keywords(prompt: str) -> List[str]:
        words = re.findall(r"\w+", prompt.lower())
        return [w for w in words if w not in LogFilter.STOP_WORDS and len(w) > 2]

    @staticmethod
    def filter_logs(logs: Iterable[Dict], prompt: str, limit: int = 50) -> List[Dict]:
        keywords = LogFilter.extract_keywords(prompt)
        logs = list(logs)
        matches = []
        for rec in logs:
            text = " ".join(
                str(rec.get(f, "")).lower() for f in
                ("containerName", "podName", "namespace", "log")
            )
            keyword_match = sum(text.count(kw) for kw in keywords)
            if keyword_match > 0:
                copy = rec.copy()
                copy["_score"] = keyword_match
                matches.append(copy)
        matches.sort(key=lambda r: -r["_score"])
        return matches[:limit]


