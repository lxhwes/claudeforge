#!/bin/bash
# ClaudeForge - Docker-based AI Agent Framework
# Usage: ./start.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "   _____ _                 _      ______                    "
    echo "  / ____| |               | |    |  ____|                   "
    echo " | |    | | __ _ _   _  __| | ___| |__ ___  _ __ __ _  ___  "
    echo " | |    | |/ _\` | | | |/ _\` |/ _ \\  __/ _ \\| '__/ _\` |/ _ \\ "
    echo " | |____| | (_| | |_| | (_| |  __/ | | (_) | | | (_| |  __/ "
    echo "  \\_____|_|\\__,_|\\__,_|\\__,_|\\___|_|  \\___/|_|  \\__, |\\___| "
    echo "                                                 __/ |      "
    echo "                                                |___/       "
    echo -e "${NC}"
    echo -e "${GREEN}Docker-based AI Agent Framework for Spec-Driven Development${NC}"
    echo ""
}

check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found${NC}"
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${RED}Please edit .env and add your ANTHROPIC_API_KEY${NC}"
        exit 1
    fi

    if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
        echo -e "${RED}Error: ANTHROPIC_API_KEY not set in .env${NC}"
        echo "Please add your Anthropic API key to the .env file"
        exit 1
    fi
}

case "$1" in
    --build|-b)
        print_banner
        check_env
        echo -e "${BLUE}Building and starting ClaudeForge...${NC}"
        docker-compose up --build -d
        echo -e "${GREEN}ClaudeForge is running!${NC}"
        echo -e "Dashboard: ${BLUE}http://localhost:5050${NC}"
        echo -e "API: ${BLUE}http://localhost:8000${NC}"
        ;;
    --stop|-s)
        echo -e "${YELLOW}Stopping ClaudeForge...${NC}"
        docker-compose down
        echo -e "${GREEN}ClaudeForge stopped.${NC}"
        ;;
    --restart|-r)
        echo -e "${YELLOW}Restarting ClaudeForge...${NC}"
        docker-compose restart
        echo -e "${GREEN}ClaudeForge restarted.${NC}"
        ;;
    --logs|-l)
        docker-compose logs -f
        ;;
    --status)
        echo -e "${BLUE}ClaudeForge Status:${NC}"
        docker-compose ps
        ;;
    --setup-auth)
        echo -e "${BLUE}API Key Setup${NC}"
        echo "1. Copy .env.example to .env: cp .env.example .env"
        echo "2. Edit .env and set ANTHROPIC_API_KEY=sk-ant-api03-your-key"
        echo "3. Run: ./start.sh --build"
        ;;
    --shell)
        echo -e "${BLUE}Opening shell in agent container...${NC}"
        docker-compose exec agent bash
        ;;
    --help|-h)
        print_banner
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  --build, -b     Build and start containers"
        echo "  --stop, -s      Stop all containers"
        echo "  --restart, -r   Restart containers"
        echo "  --logs, -l      Follow container logs"
        echo "  --status        Show container status"
        echo "  --setup-auth    Instructions for API key setup"
        echo "  --shell         Open bash in agent container"
        echo "  --help, -h      Show this help message"
        echo ""
        echo "Without arguments: Start containers (build if needed)"
        ;;
    *)
        print_banner
        check_env
        echo -e "${BLUE}Starting ClaudeForge...${NC}"
        docker-compose up -d
        echo -e "${GREEN}ClaudeForge is running!${NC}"
        echo -e "Dashboard: ${BLUE}http://localhost:5050${NC}"
        echo -e "API: ${BLUE}http://localhost:8000${NC}"
        ;;
esac
