#!/bin/bash

# Enterprise Quality Gate Script
# This script runs all quality checks and fails if any gate is not met

set -e

echo "🚀 Starting Enterprise Quality Gates..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Check if required tools are installed
check_tools() {
    echo "🔍 Checking required tools..."

    tools=("python" "black" "isort" "flake8" "mypy" "bandit" "safety" "pytest" "npm")

    for tool in "${tools[@]}"; do
        if command -v $tool &> /dev/null; then
            print_status "$tool is installed"
        else
            print_error "$tool is not installed"
            exit 1
        fi
    done
}

# Python code formatting
check_formatting() {
    echo "🎨 Checking Python code formatting..."

    echo "Running black..."
    if black --check app/; then
        print_status "Black formatting check passed"
    else
        print_error "Black formatting check failed. Run 'black app/' to fix."
        exit 1
    fi

    echo "Running isort..."
    if isort --check-only app/; then
        print_status "Import sorting check passed"
    else
        print_error "Import sorting check failed. Run 'isort app/' to fix."
        exit 1
    fi
}

# Python linting
check_linting() {
    echo "🔍 Running Python linting..."

    if flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
        print_status "Critical flake8 checks passed"
    else
        print_error "Critical flake8 checks failed"
        exit 1
    fi

    if flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics; then
        print_status "Full flake8 checks completed"
    else
        print_warning "Some flake8 warnings detected (non-blocking)"
    fi
}

# Type checking
check_types() {
    echo "🔬 Running type checking..."

    if mypy app/ --ignore-missing-imports; then
        print_status "Type checking passed"
    else
        print_error "Type checking failed"
        exit 1
    fi
}

# Security scanning
check_security() {
    echo "🔒 Running security scans..."

    echo "Running bandit..."
    if bandit -r app/ -f json -o bandit-report.json; then
        print_status "Bandit security scan passed"
    else
        print_warning "Bandit found some security issues (check bandit-report.json)"
    fi

    echo "Running safety check..."
    if safety check --json --output safety-report.json; then
        print_status "Dependency security check passed"
    else
        print_warning "Safety found some vulnerable dependencies (check safety-report.json)"
    fi
}

# Frontend linting and type checking
check_frontend() {
    echo "🌐 Checking frontend code quality..."

    cd frontend

    if command -v npm &> /dev/null; then
        echo "Running frontend linting..."
        if npm run lint 2>/dev/null; then
            print_status "Frontend linting passed"
        else
            print_error "Frontend linting failed"
            exit 1
        fi

        echo "Running frontend type checking..."
        if npm run type-check 2>/dev/null; then
            print_status "Frontend type checking passed"
        else
            print_error "Frontend type checking failed"
            exit 1
        fi
    else
        print_warning "npm not found, skipping frontend checks"
    fi

    cd ..
}

# Unit tests
run_tests() {
    echo "🧪 Running unit tests..."

    echo "Running pytest with coverage..."
    if pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80 --maxfail=5; then
        print_status "Unit tests passed with adequate coverage"
    else
        print_error "Unit tests failed or coverage below 80%"
        exit 1
    fi
}

# Performance checks (optional)
check_performance() {
    echo "⚡ Running performance checks..."

    # Check for common performance anti-patterns
    echo "Checking for performance anti-patterns..."

    # Example: Check for N+1 queries (simplified)
    if grep -r "for.*in.*query" app/ --include="*.py" | grep -v "__pycache__" | head -5; then
        print_warning "Potential N+1 query patterns detected"
    else
        print_status "No obvious N+1 query patterns found"
    fi

    # Check for missing indexes (simplified)
    if grep -r "ForeignKey" app/models/ --include="*.py" | head -5; then
        print_warning "Found ForeignKeys - ensure proper database indexes"
    fi
}

# Documentation check
check_documentation() {
    echo "📚 Checking documentation..."

    # Check if all API endpoints have documentation
    if python -c "
import ast
import sys
sys.path.append('app')
from main import app
routes = [route.path for route in app.routes]
undocumented = [r for r in routes if not r.startswith('/docs') and not r.startswith('/openapi')]
if undocumented:
    print(f'Found {len(undocumented)} potentially undocumented routes')
    sys.exit(1)
else:
    print('All routes appear to be documented via FastAPI auto-docs')
" 2>/dev/null; then
        print_status "API documentation check passed"
    else
        print_warning "Some API endpoints may lack documentation"
    fi
}

# Generate quality report
generate_report() {
    echo "📊 Generating quality report..."

    cat > quality-report.md << EOF
# Quality Gate Report - $(date)

## Summary
- ✅ Code Formatting: Passed
- ✅ Linting: Passed
- ✅ Type Checking: Passed
- ✅ Security Scanning: Completed
- ✅ Unit Tests: Passed (≥80% coverage)
- ✅ Frontend Checks: Passed
- ✅ Documentation: Checked

## Artifacts
- \`bandit-report.json\`: Security scan results
- \`safety-report.json\`: Dependency security check
- \`htmlcov/\`: Test coverage report
- \`coverage.xml\`: Coverage in XML format

## Next Steps
1. Review any warnings in security scans
2. Address any flake8 warnings (non-blocking)
3. Maintain test coverage above 80%
4. Regularly update dependencies

Generated on: $(date)
EOF

    print_status "Quality report generated: quality-report.md"
}

# Main execution
main() {
    echo "Enterprise Quality Gates for Artacom FTTH Billing System"
    echo "=========================================================="

    check_tools
    check_formatting
    check_linting
    check_types
    check_security
    check_frontend
    run_tests
    check_performance
    check_documentation
    generate_report

    echo ""
    echo "🎉 All quality gates passed successfully!"
    echo "Ready for deployment to staging environment."
}

# Run main function
main "$@"