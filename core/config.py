import os
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# Safety patterns — block harmful / off-topic content
BLOCKED_PATTERNS: List[Tuple[str, str]] = [
    ("violence", r"\b(kill|murder|torture|bomb|explosive|weapon\s*mass)\b"),
    ("self_harm", r"\b(suicide|self-harm|self-harm|cut\s*myself|end\s+my\s+life)\b"),
    ("harassment", r"\b(stupid|idiot|moron|retard)\b.*\b(you|your)\b"),
    ("hate_speech", r"\b(nazi|white\s+supremacy|racial\s+purity)\b"),
    ("explicit_adult", r"\b(porn|sexual\s+content|nsfw|xxx)\b"),
    ("drugs", r"\b(meth|heroin|cocaine|lsd|synthesize\s+drugs)\b"),
    ("weapons", r"\b(3d\s*print\s+gun|build\s+a\s+bomb|make\s+explosive)\b"),
    ("illegal_access", r"\b(hack\s+into|steal\s+password|crack\s+license|ddos\s+attack)\b"),
    ("phishing", r"\b(create\s+phishing|build\s+phishing|phishing\s+page|fake\s+login\s+page)\b"),
]

# Prompt injection + jailbreak patterns
INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(directions|commands|rules)",
    r"(reveal|show|display|print|output)\s+(your\s+)?(system\s+)?prompt",
    r"(reveal|show|display|output)\s+(your\s+)?(internal|hidden|secret)\s+(instructions|directions)",
    r"(forget|disregard|override|bypass)\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|guidelines)",
    r"you\s+(are\s+)?(now|will\s+now)\s+(act\s+as|become|are\s+free|are\s+released)",
    r"(do\s+not\s+follow|ignore|skip)\s+(your\s+)?(safety|guidelines|rules|restrictions)",
    r"from\s+now\s+on\s+(you\s+are|you\'?re)\s+",
    r"you\s+(don\'?t\s+)?(have\s+to|need\s+not)\s+follow",
    r"this\s+is\s+(a\s+)?(test|simulation|hypothetical|roleplay|fictional)",
    r"DAN|do\s+anything\s+now",
    r"you\s+(are\s+)?(now\s+)?DAN",
    r"bypass\s+(all\s+)?(restrictions|filters|limitations)",
    r"no\s+(restrictions|limits|boundaries|rules)",
    r"unfiltered|uncensored|unjailbroken",
    r"you\s+(must\s+)?(answer|respond)\s+(regardless|without\s+restriction)",
    r"you\s+(have\s+)?(no\s+)?(ethical|moral)\s+(guidelines|boundaries|limits)",
    r"you\s+(are\s+)?(now\s+)?a\s+free\s+((language\s+)?model|ai|assistant)",
    r"respond\s+in\s+base64|encoded\s+query|reverse\s+prompt",
    r"((sorry|apologize)\s+)?i\s+(can'?t|won'?t|cannot)\s+(comply|answer|respond)",
    r"pretend\s+(you\s+are|to\s+be|that)",
    r"act\s+as\s+(if|though)\s+(you\s+are|your)",
    r"hypothetical:\s*how\s+(would|to|could|can).{0,50}(hack|bypass|exploit)",
]

# PII patterns
PII_PATTERNS: List[Tuple[str, str]] = [
    ("email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ("phone", r"(?<!\d)(\+?\d{1,3}[-.\s]?)?\d{9,12}(?!\d)"),
    ("cccd", r"\b\d{9}\b|\b\d{12}\b"),
]

# Cyber Security keywords for topic validation
SECURITY_KEYWORDS: List[str] = [
    "malware", "ransomware", "phishing", "vulnerability", "cve", "exploit",
    "firewall", "encryption", "authentication", "authorization", "penetration",
    "intrusion", "ddos", "botnet", "trojan", "worm", "spyware", "rootkit",
    "backdoor", "keylogger", "social engineering", "zero-day", "payload",
    "shellcode", "buffer overflow", "sql injection", "xss", "csrf",
    "network security", "cyber", "hacker", "cybersecurity",
    "security audit", "risk assessment", "threat intelligence",
    "incident response", "forensics", "security policy", "access control",
    "cryptography", "hash", "digital signature", "certificate",
    "ssl", "tls", "vpn", "ids", "ips", "siem", "soc", "waf",
    "owasp", "nist", "iso 27001", "pci dss", "gdpr",
    "privilege escalation", "lateral movement", "persistence",
    "command and control", "data exfiltration", "reconnaissance",
    "osint", "threat actor", "apt", "indicator of compromise",
    "packet analysis", "network scan", "port scan", "sniffing",
    "spoofing", "man-in-the-middle", "session hijacking",
    "password cracking", "brute force", "dictionary attack",
    "sandbox", "honeypot", "deception", "security control",
    "compliance", "governance", "security framework",
    "penetration testing", "red team", "blue team", "purple team",
    "c2 server", "beacon", "dropper", "loader", "stager",
    "mimikatz", "metasploit", "cobalt strike", "empire",
    "bloodhound", "responder", "impacket", "powershell empire",
    "active directory", "kerberos", "ntlm", "ldap", "saml",
    "oauth", "zero trust", "defense in depth", "least privilege",
    "segmentation", "microsegmentation", "edr", "xdr", "mdr",
    "soar", "tipping", "user behavior analytics", "ueba",
    "dark web", "exploit kit", "malvertising", "drive-by download",
    "watering hole", "spear phishing", "whaling", "vishing", "smishing",
    "security", "cyber attack", "data breach", "vulnerability assessment",
    "threat hunting", "cryptographic", "public key", "private key",
    "certificate authority", "pkcs", "secure coding", "security testing",
    "code review", "security architecture", "security operations",
    "incident handling", "malware analysis", "reverse engineering",
    "binary exploitation", "heap overflow", "stack overflow", "format string",
    "race condition", "side channel", "timing attack", "replay attack",
    "birthday attack", "rainbow table", "salt", "iv", "nonce",
    "cipher", "aes", "rsa", "ecc", "dsa", "hmac", "sha",
    "security header", "content security policy", "cors", "hsts",
    "sqlmap", "nmap", "wireshark", "burp suite", "hydra", "john",
    "hashcat", "aircrack", "netcat", "socat", "ngrok", "chisel",
    "ligolo", "fragment", "payload", "shell", "webshell",
    "reverse shell", "bind shell", "staged payload", "stageless payload",
    "msfvenom", "custom payload", "obfuscation", "encoding",
    "base64", "hex encoding", "xor encoding", "caesar cipher",
    "vigenere", "rot13", "substitution cipher", "transposition cipher",
    "block cipher", "stream cipher", "symmetric encryption",
    "asymmetric encryption", "hybrid encryption", "key exchange",
    "diffie-hellman", "elliptic curve", "quantum cryptography",
    "post-quantum", "lattice-based", "hash-based",
    "digital forensics", "memory forensics", "disk forensics",
    "network forensics", "mobile forensics", "cloud forensics",
    "chain of custody", "forensic imaging", "file carving",
    "steganography", "covert channel", "data hiding",
    "traffic analysis", "netflow", "packet capture", "pcap",
    "@stake", "guardium", "appscan", "fortify", "checkmarx",
    "sonarqube", "dependency check", "sast", "dast", "iast", "rast",
]

@dataclass
class ModelInfo:
    name: str
    category: str
    description: str
    display_name: str = ""

MODEL_CATALOG: List[ModelInfo] = [
    ModelInfo("qwen2:7b", "General", "Qwen2 7B local model (default)"),
    ModelInfo("minimax-m3:cloud", "General", "MiniMax M3 Cloud"),
    ModelInfo("llama3.2:1b", "General", "Meta Llama 3.2 1B lightweight"),
    ModelInfo("llama3.2:3b", "General", "Meta Llama 3.2 3B fast"),
    ModelInfo("llama3.1:8b", "General", "Meta Llama 3.1 8B"),
    ModelInfo("llama3.1:70b", "General", "Meta Llama 3.1 70B"),
    ModelInfo("llama3:70b", "General", "Meta Llama 3 70B"),
    ModelInfo("mistral:7b", "General", "Mistral 7B"),
    ModelInfo("mistral-nemo:12b", "General", "Mistral Nemo 12B"),
    ModelInfo("qwen2.5:0.5b", "General", "Qwen 2.5 0.5B"),
    ModelInfo("qwen2.5:1.5b", "General", "Qwen 2.5 1.5B"),
    ModelInfo("qwen2.5:3b", "General", "Qwen 2.5 3B"),
    ModelInfo("qwen2.5:7b", "General", "Qwen 2.5 7B"),
    ModelInfo("qwen2.5:14b", "General", "Qwen 2.5 14B"),
    ModelInfo("qwen2.5:32b", "General", "Qwen 2.5 32B"),
    ModelInfo("qwen2.5:72b", "General", "Qwen 2.5 72B"),
    ModelInfo("gemma2:2b", "General", "Google Gemma 2 2B"),
    ModelInfo("gemma2:9b", "General", "Google Gemma 2 9B"),
    ModelInfo("gemma2:27b", "General", "Google Gemma 2 27B"),
    ModelInfo("phi3:3.8b", "General", "Phi-3 3.8B mini"),
    ModelInfo("phi3:14b", "General", "Phi-3 14B medium"),
    ModelInfo("phi3.5:3.8b", "General", "Phi-3.5 3.8B"),
    ModelInfo("falcon3:7b", "General", "Falcon3 7B"),
    ModelInfo("falcon3:10b", "General", "Falcon3 10B"),
    ModelInfo("neural-chat:7b", "General", "Intel Neural Chat 7B"),
    ModelInfo("solar:10.7b", "General", "Solar 10.7B"),
    ModelInfo("tinyllama:1.1b", "Lightweight", "TinyLlama 1.1B"),
    ModelInfo("orca-mini:3b", "Lightweight", "Orca Mini 3B"),
    ModelInfo("codellama:7b", "Code", "Code Llama 7B"),
    ModelInfo("codellama:13b", "Code", "Code Llama 13B"),
    ModelInfo("codellama:34b", "Code", "Code Llama 34B"),
    ModelInfo("deepseek-coder:6.7b", "Code", "DeepSeek Coder 6.7B"),
    ModelInfo("deepseek-coder:33b", "Code", "DeepSeek Coder 33B"),
    ModelInfo("starcoder2:3b", "Code", "StarCoder2 3B"),
    ModelInfo("starcoder2:7b", "Code", "StarCoder2 7B"),
    ModelInfo("starcoder2:15b", "Code", "StarCoder2 15B"),
    ModelInfo("codeqwen:7b", "Code", "CodeQwen 7B"),
    ModelInfo("llava:7b", "Vision", "LLaVA 7B multimodal"),
    ModelInfo("llava:13b", "Vision", "LLaVA 13B"),
    ModelInfo("llava:34b", "Vision", "LLaVA 34B"),
    ModelInfo("bakllava:7b", "Vision", "BakLLaVA 7B"),
    ModelInfo("nomic-embed-text", "Embedding", "Nomic Embed Text 1.5"),
    ModelInfo("all-minilm", "Embedding", "All-MiniLM-L6-v2"),
    ModelInfo("deepseek-r1:7b", "Math", "DeepSeek R1 7B"),
    ModelInfo("deepseek-r1:14b", "Math", "DeepSeek R1 14B"),
    ModelInfo("deepseek-r1:32b", "Math", "DeepSeek R1 32B"),
    ModelInfo("deepseek-r1:70b", "Math", "DeepSeek R1 70B"),
    ModelInfo("mathstral:7b", "Math", "Mathstral 7B"),
    ModelInfo("dolphin-mistral:7b", "Creative", "Dolphin Mistral 7B"),
    ModelInfo("dolphin-mixtral:8x7b", "Creative", "Dolphin Mixtral 8x7B"),
    ModelInfo("nous-hermes2:10b", "Creative", "Nous Hermes 2 10B"),
]

MODEL_CATEGORIES: List[str] = [
    "General", "Code", "Vision", "Embedding", "Math", "Creative", "Lightweight",
]

@dataclass
class AgentConfig:
    max_history_messages: int = 50
    max_context_tokens: int = 4096
    default_max_tokens: int = field(default_factory=lambda: env_int("DEFAULT_MAX_TOKENS", 2048, 64, 32768))
    max_response_tokens: int = field(default_factory=lambda: env_int("MAX_RESPONSE_TOKENS", 8192, 64, 32768))
    max_plan_steps: int = 5
    max_retries: int = 3
    memory_enabled: bool = True
    safety_enabled: bool = True
    audit_enabled: bool = True
    loop_detection_enabled: bool = True
    output_validation_enabled: bool = True
    goal_tracking_enabled: bool = False
    planning_enabled: bool = False
    adaptive_scale: bool = True

    # Token costs (approximate, per model)
    model_costs: dict = field(default_factory=lambda: {
        "llama3.2": {"input": 0.0, "output": 0.0},
        "llama3.1": {"input": 0.0, "output": 0.0},
        "mistral": {"input": 0.0, "output": 0.0},
        "codellama": {"input": 0.0, "output": 0.0},
        "default": {"input": 0.0, "output": 0.0},
    })

    # Complexity heuristic
    short_query_max_words: int = 10
    complex_query_min_words: int = 50


def estimate_tokens(text: str) -> int:
    return len(text) // 4 + 1


def env_int(name: str, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(min_value, min(value, max_value))


def clamp_max_tokens(value: int, config: AgentConfig | None = None) -> int:
    cfg = config or AgentConfig()
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = cfg.default_max_tokens
    return max(1, min(value, cfg.max_response_tokens))


def estimate_model_cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    config: AgentConfig | None = None,
) -> float:
    cfg = config or AgentConfig()
    costs = cfg.model_costs or {}
    selected = costs.get("default", {"input": 0.0, "output": 0.0})
    model_lower = (model or "").lower()
    for prefix, pricing in costs.items():
        if prefix != "default" and model_lower.startswith(prefix.lower()):
            selected = pricing
            break
    return round(
        (input_tokens / 1000.0) * float(selected.get("input", 0.0))
        + (output_tokens / 1000.0) * float(selected.get("output", 0.0)),
        8,
    )
