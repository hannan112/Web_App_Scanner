# Docker Configuration for Security Scanner

This directory contains the Docker configuration for the security scanner with a **hybrid approach** for discovery tools.

## 🏗️ Architecture

### **Hybrid Tool Strategy**
- **Local Tools**: subfinder, nuclei, feroxbuster, waybackurls (installed locally)
- **Docker Tools**: httpx, katana, gospider (running in containers)
- **Seamless Integration**: Wrapper scripts provide unified interface

## 📦 Services

### **Core Services**
1. **web** - Django backend application
2. **db** - PostgreSQL database
3. **zap** - OWASP ZAP for security scanning
4. **discovery-tools** - Enhanced discovery tools container
5. **pgadmin** - Database management (optional)

### **Discovery Tools Container**
The `discovery-tools` service includes:
- ✅ **httpx** - HTTP probing and technology detection
- ✅ **katana** - Modern web crawler with JavaScript support
- ✅ **gospider** - Fast web crawler
- ✅ **nuclei** - Vulnerability scanner
- ✅ **subfinder** - Subdomain discovery
- ✅ **waybackurls** - Historical URL discovery
- ✅ **feroxbuster** - Directory and file discovery

## 🚀 Quick Start

### **1. Build and Start Services**
```bash
cd docker-containers
docker-compose up -d
```

### **2. Setup Discovery Tools**
```bash
./setup-discovery-tools.sh
```

### **3. Verify Installation**
```bash
# Check local tools
subfinder --version
nuclei --version
feroxbuster --version
waybackurls --version

# Check Docker tools (via wrappers)
httpx --version
katana --version
gospider --version
```

## 🔧 Configuration

### **Environment Variables**
```yaml
# Web Service
DATABASE_URL: postgres://scanner:scanner@db:5432/scanner
ZAP_HOST: zap
ZAP_PORT: 8080
ZAP_API_KEY: changeme123

# Discovery Tools
ENABLE_ACTIVE_SCANNING: true
MAX_CONCURRENT_ACTIVE_SCANS: 3
ACTIVE_SCAN_TIMEOUT_MINUTES: 60
```

### **Volumes**
- `postgres_data` - Database persistence
- `zap_data` - ZAP session data
- `discovery_data` - Discovery tool data
- `logs_volume` - Application logs

## 🛠️ Tool Integration

### **Local Tools** (Direct execution)
```python
# These run directly on the host
subfinder -d example.com
nuclei -u https://example.com
feroxbuster --url https://example.com
waybackurls example.com
```

### **Docker Tools** (Via wrappers)
```python
# These run in Docker containers
httpx -l targets.txt -tech-detect
katana -u https://example.com -js-crawl
gospider -s https://example.com
```

### **Code Integration**
The scanner automatically detects tool availability:
```python
# Enhanced discovery engine
tools = {
    'nuclei': self._check_tool('nuclei'),      # Local
    'httpx': self._check_tool('httpx'),       # Docker wrapper
    'katana': self._check_tool('katana'),     # Docker wrapper
    'subfinder': self._check_tool('subfinder'), # Local
    'gospider': self._check_tool('gospider')  # Docker wrapper
}
```

## 📊 Performance Benefits

### **Local Tools** (Faster)
- Direct binary execution
- No container overhead
- Better file system access
- Lower resource usage

### **Docker Tools** (Reliable)
- No system dependencies
- Always up-to-date
- Isolated environment
- Easy cleanup

## 🔍 Discovery Workflow

### **Phase 1: Subdomain Discovery**
```bash
subfinder -d example.com -silent -json
```

### **Phase 2: Technology Detection**
```bash
httpx -l targets.txt -tech-detect -json
```

### **Phase 3: Web Crawling**
```bash
katana -u https://example.com -js-crawl -depth 3
```

### **Phase 4: Historical URLs**
```bash
waybackurls example.com
```

### **Phase 5: Directory Discovery**
```bash
feroxbuster --url https://example.com --json
```

### **Phase 6: Vulnerability Scanning**
```bash
nuclei -u https://example.com -templates discovery/
```

## 🐛 Troubleshooting

### **Common Issues**

1. **Docker tools not working**
   ```bash
   # Check if discovery-tools container is running
   docker ps | grep discovery-tools
   
   # Restart if needed
   docker-compose restart discovery-tools
   ```

2. **Local tools missing**
   ```bash
   # Check tool availability
   which subfinder nuclei feroxbuster waybackurls
   
   # Install missing tools
   ./setup-discovery-tools.sh
   ```

3. **Permission issues**
   ```bash
   # Fix script permissions
   chmod +x scripts/*
   chmod +x setup-discovery-tools.sh
   ```

### **Logs and Debugging**
```bash
# View service logs
docker-compose logs web
docker-compose logs discovery-tools

# Check tool availability
docker exec discovery-tools_1 httpx --version
docker exec discovery-tools_1 katana --version
```

## 📈 Monitoring

### **Health Checks**
- ZAP: `http://localhost:8080/JSON/core/view/version/`
- Database: Automatic connection testing
- Discovery Tools: Container status monitoring

### **Resource Usage**
```bash
# Monitor container resources
docker stats

# Check disk usage
docker system df
```

## 🔄 Updates

### **Update Docker Images**
```bash
docker-compose pull
docker-compose up -d
```

### **Update Local Tools**
```bash
# Update Go-based tools
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

## 🎯 Best Practices

1. **Use local tools when available** - Better performance
2. **Fall back to Docker** - When local tools are missing
3. **Monitor resource usage** - Docker containers use more resources
4. **Keep tools updated** - Regular updates for security
5. **Use wrapper scripts** - Consistent interface across tools

## 📝 Notes

- The hybrid approach provides the best of both worlds
- Local tools are faster but require system dependencies
- Docker tools are more reliable but have overhead
- Wrapper scripts provide seamless integration
- All tools work together in the discovery pipeline

