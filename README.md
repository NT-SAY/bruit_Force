# Ultimate BruteForcer - AI-Powered Password Cracking Tool

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Async](https://img.shields.io/badge/Async-Yes-brightgreen.svg)](https://docs.python.org/3/library/asyncio.html)
[![Multi-processing](https://img.shields.io/badge/Multi--processing-Yes-orange.svg)](https://docs.python.org/3/library/multiprocessing.html)

An intelligent, high-performance brute force tool with AI-powered time estimation, adaptive strategies, and CPU acceleration.

## 🚀 Features

- **🤖 AI-Powered Time Estimation** - Predicts attack duration and feasibility
- **⚡ CPU Acceleration** - Multi-processing and vectorized operations
- **🌐 Smart Proxy Management** - Automatic proxy verification and rotation
- **🎯 Adaptive Strategies** - Real-time protection detection and evasion
- **📊 Intelligent Analysis** - Pre-attack feasibility assessment
- **🔧 Rule-Based Enhancement** - Advanced password mutation rules
- **💾 Progress Saving** - Resume attacks from last checkpoint

## 📋 Supported Attack Types

- **Hash Cracking** (MD5, SHA1, SHA256)
- **Web Form Brute Force**
- **SSH Brute Force** (Planned)
- **API Endpoint Attacks** (Planned)

## 🛠 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ultimate-bruteforcer.git
cd ultimate-bruteforcer

# Install dependencies
pip install -r requirements.txt
Dependencies
bash
pip install aiohttp aiohttp-socks fake-useragent uvloop numpy
📖 Usage------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Basic Hash Attack
bash
python bruteforcer.py --target 5f4dcc3b5aa765d61d8327deb882cf99 --type hash --wordlist passwords.txt
Web Form Attack
bash
python bruteforcer.py --target https://example.com/login --type web --wordlist passwords.txt --username admin
With Proxies
bash
python bruteforcer.py --target https://example.com/login --type web --wordlist passwords.txt --proxies proxies.txt
⚙️ Configuration----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Command Line Arguments
Argument	Description	Required
--target	Target hash or URL	Yes
--type	Attack type (hash, web, ssh)	Yes
--wordlist	Path to password wordlist	Yes
--username	Username for authentication	No
--proxies	Path to proxies file	No
Wordlist Format
Plain text file with one password per line:

text
password
123456
admin
qwerty
...
Proxies Format
Plain text file with one proxy per line (SOCKS/HTTP):

text
socks5://user:pass@host:port
http://user:pass@host:port
socks4://host:port
🧠 Intelligent Features---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Time Estimation
Predicts attack duration based on wordlist size and hardware

Provides feasibility analysis before starting

Recommends optimization strategies

Adaptive Strategies
Detects protection mechanisms (Cloudflare, CAPTCHA, WAF)

Automatically adjusts request rates and patterns

Rotates proxies and user agents intelligently

Performance Optimization
Multi-process CPU acceleration

Vectorized hash computations

Batch processing for efficiency

📊 Performance Metrics----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Operation	Speed	Hardware
MD5 Hashing	5M hashes/sec	CPU
MD5 Hashing	10B hashes/sec	GPU (Theoretical)
Web Requests	10-50 reqs/sec	With proxies
🔧 Advanced Configuration-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Custom Rules
Modify the RuleEngine class to add custom password mutation rules:

python
# Add custom suffixes and prefixes
common_suffixes = ['123', '!', '@', '#', '2023']
common_prefixes = ['admin', 'root', 'super']
Strategy Tuning
Adjust adaptive strategies in AdaptiveStrategyManager:

python
strategies = {
    ProtectionLevel.NONE: {'delay': 0.01, 'concurrency': 100},
    ProtectionLevel.WEAK: {'delay': 0.1, 'concurrency': 50},
    # ... more levels
}
⚠️ Legal Disclaimer-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
This tool is intended for:

Educational purposes

Security research

Authorized penetration testing

System security assessments

⚠️ IMPORTANT: Always obtain proper authorization before testing any system. Unauthorized access to computer systems is illegal and unethical.

The developers are not responsible for misuse of this tool.

🎯 Roadmap----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
GPU acceleration support

SSH brute force implementation

API endpoint attacks

Distributed computing support

GUI interface

More hash algorithms

Password pattern analysis

🤝 Contributing-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
We welcome contributions! Please feel free to submit pull requests, open issues, or suggest new features.

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Built with Python AsyncIO for high performance

Uses NumPy for vectorized computations

Inspired by modern penetration testing tools

Thanks to all contributors and testers



P.S. This project is currently under active development and may contain some bugs or unfinished features. Your feedback and contributions are welcome!

P.P.S. This project was created with assistance from AI language models to help with code generation and documentation.
