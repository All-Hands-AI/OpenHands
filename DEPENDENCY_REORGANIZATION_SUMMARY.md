# OpenHands Dependency Reorganization - Executive Summary

## 🎯 Objective
Transform OpenHands from a monolithic dependency structure to a flexible, extras-based installation system that allows users to install only the components they need.

## 📊 Current State Analysis

### Package Structure
- **230 total modules** analyzed across 15 main packages
- **Core packages** (events, llm, runtime, controller, critic, agenthub, integrations, storage, security, memory, microagent, mcp, core, utils) - always included
- **Optional feature packages** (cli, resolver, server) - can be installed separately

### Dependency Issues Identified
1. **Monolithic Installation**: ~500MB installation with all dependencies
2. **Unused Dependencies**: Many users install heavy deps they never use
3. **Conflicting Requirements**: Different environments need different deps
4. **Development Overhead**: Contributors must install everything

## 🏗️ Proposed Solution: Single Package with Multiple Extras

### Core Installation (Always Required)
```bash
pip install openhands-ai  # Includes all core packages: events, llm, runtime, controller,
                         # critic, agenthub, integrations, storage, security, memory,
                         # microagent, mcp, core, utils
```

### Optional Feature Packages
```bash
pip install openhands-ai[cli]        # Command-line interface
pip install openhands-ai[resolver]   # Issue resolution functionality
pip install openhands-ai[server]     # Web server and API
```

### Optional Heavy Dependencies (for core functionality)
```bash
pip install openhands-ai[docker]     # Docker runtime support
pip install openhands-ai[kubernetes] # Kubernetes runtime support
pip install openhands-ai[browser]    # Browser automation
pip install openhands-ai[files]      # Document processing
pip install openhands-ai[aws]        # AWS integrations
pip install openhands-ai[google]     # Google Cloud integrations
pip install openhands-ai[storage]    # Redis, Minio storage backends
```

### Convenience Combinations
```bash
pip install openhands-ai[local]      # docker + files
pip install openhands-ai[web]        # server + browser + files
pip install openhands-ai[cloud]      # aws + google + azure + storage
pip install openhands-ai[full]       # everything (current behavior)
```

## 🔍 Key Findings from Analysis

### Dependency Mapping by Usage
- **Docker**: Only used in 7 files (runtime/impl/docker/, server/conversation_manager/)
- **FastAPI**: Only used in 25 files (server/, runtime/action_execution_server.py)
- **Kubernetes**: Only used in 1 file (runtime/impl/kubernetes/)
- **BrowserGym**: Only used in 5 files (runtime/browser/, agenthub/*browsing*)
- **File Processing**: Only used in 1 file (runtime/plugins/agent_skills/file_reader/)

### Import Relationship Analysis
```
Revised dependency flow:
Core (always included):
├── Events (foundation for everything)
├── LLM (used by 9+ packages)
├── Runtime (used by 7+ packages)
├── Controller (orchestrates agents)
├── Critic (evaluates agent performance)
├── AgentHub (agent implementations)
├── Integrations (third-party services)
├── Storage (data persistence)
├── Security (security features)
├── Memory (memory management)
├── Microagent (microagent system)
├── MCP (Model Context Protocol)
├── Core (configuration)
└── Utils (shared utilities)

Optional Features:
├── CLI (command-line interface)
├── Resolver (issue resolution)
└── Server (web API)
```

## 🚀 Implementation Plan

### Phase 1: Code Refactoring (2-3 weeks)
1. **Add import guards** for optional dependencies
2. **Implement graceful degradation** when deps missing
3. **Create feature detection** utilities
4. **Update error messages** with installation hints

### Phase 2: pyproject.toml Reorganization (1 week)
1. **Move dependencies to optional** sections
2. **Define extras groups** with logical groupings
3. **Update CI/CD** to test different combinations
4. **Create validation scripts**

### Phase 3: Testing & Documentation (2 weeks)
1. **Comprehensive test matrix** for all extras combinations
2. **Update installation guides** with new options
3. **Create migration guide** for existing users
4. **Add troubleshooting documentation**

### Phase 4: Rollout (1-2 weeks)
1. **Beta release** with backwards compatibility
2. **Gather user feedback** and iterate
3. **Full release** with new default behavior
4. **Deprecate old patterns** over time

## 📈 Expected Benefits

### For Users
- **Comprehensive core** with all essential functionality included
- **Optional features** can be added as needed (CLI, resolver, server)
- **Optional heavy dependencies** for specialized functionality (Docker, cloud services)
- **Clearer feature boundaries** and installation options

### For Developers
- **Focused development** environments
- **Faster CI/CD** with targeted testing
- **Better separation** of concerns
- **Easier maintenance** of specific features

### For the Project
- **Cleaner architecture** with core vs optional features
- **Better modularity** for adding new functionality
- **Easier maintenance** of optional components
- **More sustainable** dependency management

## 🛠️ Technical Implementation Highlights

### Optional Dependency Pattern
```python
from openhands.utils.import_utils import get_optional_dependency

docker_dep = get_optional_dependency('docker')

class DockerRuntime:
    def __init__(self):
        self.docker = docker_dep.require()  # Raises helpful error if missing
```

### Feature Detection
```python
from openhands.core.features import FeatureManager

features = FeatureManager.get_available_features()
# {'docker_runtime': True, 'web_server': False, ...}
```

### Graceful Error Messages
```
ImportError: docker is required for Docker runtime support.
Install with: pip install openhands-ai[runtime]
```

## 📋 Next Steps

1. **Review and approve** this analysis and implementation plan
2. **Create GitHub issues** for each phase of implementation
3. **Set up project board** to track progress
4. **Begin Phase 1** code refactoring work
5. **Establish testing infrastructure** for extras validation

## 🎯 Success Metrics

- **Cleaner architecture**: Clear separation between core and optional features
- **Installation flexibility**: Users can install exactly what they need
- **Reduced dependency conflicts**: Heavy dependencies are optional
- **User satisfaction**: Positive feedback on installation options
- **Developer productivity**: Faster development environment setup for focused work
- **CI/CD efficiency**: Ability to test different feature combinations

---

**Files Created:**
- `dependency_analysis.md` - Detailed technical analysis
- `implementation_guide.md` - Step-by-step implementation instructions
- `DEPENDENCY_REORGANIZATION_SUMMARY.md` - This executive summary

**Ready for implementation!** 🚀
