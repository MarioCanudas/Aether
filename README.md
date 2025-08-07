# Aether_v1

Aether_v1 is a comprehensive financial analysis platform that processes bank statements from multiple Mexican banks. The application features an advanced document processing pipeline with direct PDF text extraction, table reconstruction, and financial analysis capabilities through a modern Streamlit web interface. It supports **Banorte**, **BBVA**, **Nu Bank**, **Banamex**, **HSBC**, and **Inbursa** statements across both debit and credit card formats, with intelligent text processing and automated transaction categorization.

## Table of Contents

- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
  - [1. Installation](#1-installation)
  - [2. Run the Application](#2-run-the-application)
  - [3. Using the Interface](#3-using-the-interface)
- [Supported Banks](#supported-banks)
- [Features](#features)
- [Testing](#testing)
- [Project Architecture](#project-architecture)
- [License](#license)

---

## Project Structure

The project follows a modular MVC architecture with clear separation of concerns:

```bash
/Aether_v1
│
├── /config               # Configuration settings and constants
├── /controllers          # MVC Controllers for business logic
│   ├── analysis_controller.py      # Financial analysis operations
│   ├── base_controller.py          # Base controller with database scoping
│   └── transaction_processor_controller.py # Transaction processing logic
├── /core                 # Core interfaces and abstract classes
├── /documents            # Document storage (gitignored except test files)
├── /frontend             # Streamlit web application
│   ├── /assets           # Static files (logos, images)
│   ├── /views            # Individual page views
│   │   ├── home.py                  # Main dashboard with financial overview
│   │   ├── transaction_processor.py # Document upload and processing
│   │   ├── income_analysis.py      # Income analysis and visualization
│   │   ├── expenses_analysis.py    # Expense analysis and visualization
│   │   ├── data.py                 # Data export and management
│   │   └── cash_transaction.py     # Manual transaction entry
│   └── app.py            # Main Streamlit application entry point
├── /models               # Data processing and analysis models
│   ├── /core             # Core interfaces and abstract classes
│   ├── /document_processing # PDF reading, text extraction, and processing
│   ├── /table_processing # Table reconstruction and data extraction
│   └── /data_processing  # Data normalization and export
├── /services             # Business logic services
│   ├── data_processing_service.py   # Data processing operations
│   ├── financial_analysis_service.py # Financial analysis calculations
│   └── plotting_service.py          # Chart and visualization generation
├── /tests                # Comprehensive test suite
│   ├── /test_data        # Test files for all supported banks
│   ├── /test_models      # Unit tests for model layer
│   ├── /test_services    # Unit tests for service layer
│   └── /test_controllers # Unit tests for controller layer
├── /utils                # Utility functions and helpers
├── pyproject.toml        # Modern Python project configuration
├── requirements.txt      # Production dependencies
└── README.md             # Project documentation
```
---

## Requirements

The project requires **Python 3.9+** and the following dependencies:

### Core Dependencies
- `streamlit==1.44.1` - Web application framework
- `pandas==2.2.3` - Data manipulation and analysis
- `matplotlib==3.10.1` - Data visualization and plotting
- `pdfplumber==0.11.6` - PDF text and coordinate extraction (primary document processing)
- `easyocr==1.7.2` - Optical Character Recognition (fallback for image-based PDFs)
- `scikit-learn==1.6.1` - Machine learning utilities for data analysis

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `poe-the-poet>=0.24.0` - Task runner

To install the dependencies, run:

```bash
pip install -r requirements.txt
```

For development, install additional dependencies:
```bash
pip install -e ".[dev,test]"
```
## How to Run

### 1. Installation
Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd Aether/Aether_v1
pip install -r requirements.txt
```

### 2. Run the Application
Start the Streamlit web application:

```bash
streamlit run frontend/app.py
```

Or using the project task runner:
```bash
poe run-app
```

### 3. Using the Interface
1. **Access the App**: Open your browser and navigate to `http://localhost:8501`
2. **Upload Documents**: Use the file uploader to select one or more bank statement PDFs
3. **View Analysis**: The app will automatically process the documents and display:
   - Financial health metrics and scoring
   - Monthly savings analysis
   - Income and expense breakdowns
   - Interactive charts and visualizations
4. **Navigate**: Use the sidebar to access different analysis views:
   - **Overview**: Main dashboard with financial health score
   - **Transaction Processor**: Detailed processing and raw data view
   - **Income Analysis**: Income trends and patterns
   - **Expenses Analysis**: Expense categorization and trends
   - **Data Export**: Export processed data to CSV

## Supported Banks

The application currently supports the following Mexican banks with intelligent format detection:

### Fully Supported Banks
**Banorte**
- **Debit Cards**: Complete transaction history with balance tracking
- **Credit Cards**: 
  - Legacy format support
  - New format (2024+) with enhanced date parsing
  - Automatic format detection

**BBVA**
- **Debit Cards**: Full transaction processing with categorization
- **Credit Cards**: Charge and payment tracking
- **New Credit Format**: Enhanced format support (2024+)

**Nu Bank**
- **Debit Cards**: Account movement tracking and analysis
- **Credit Cards**: Transaction processing with period analysis

**Banamex**
- **Credit Cards**: Legacy and new format support

**HSBC**
- **Credit Cards**: Transaction processing and categorization

**Inbursa**
- **Debit Cards**: Complete account movement tracking
- **Credit Cards**: Transaction analysis with promotional tracking

### Banks in Development
- **American Express (AMEX)**: Basic structure implemented, full processing in development
- **Santander**: Bank properties being configured
- **Banamex Debit**: Under development

Each supported bank's statements are processed using specific extraction rules that handle:
- Date format variations (DD/MM/YY, DD-MMM-YYYY, etc.)
- Amount parsing with currency symbols and signs
- Transaction categorization (income vs. expenses)
- Balance calculations and verification
- Period detection and year inference
## Features

### Document Processing
- **Direct PDF Text Extraction**: PDFPlumber-based text extraction with precise coordinate mapping from text-based PDFs
- **Intelligent Table Reconstruction**: Automatic detection and reconstruction of transaction tables using coordinate-based analysis
- **Multi-Bank Support**: Handles different statement formats from major Mexican banks with bank-specific processing rules
- **Text Processing Pipeline**: Advanced text correction and normalization for improved data quality
- **Batch Processing**: Upload and process multiple statements simultaneously

### Financial Analysis
- **Health Scoring**: Comprehensive financial health assessment with visual indicators
- **Savings Tracking**: Monthly savings calculation and trend analysis
- **Income Analysis**: Detailed income pattern recognition and forecasting
- **Expense Categorization**: Automatic expense classification and trend analysis
- **Monthly Metrics**: Average income, expenses, and savings per month

### Data Management
- **In-Memory Processing**: Session-based data processing and storage (primary mode)
- **Data Export**: Export processed data to CSV format
- **Session State Management**: Maintain processed data across user sessions using Streamlit session state
- **Data Validation**: Comprehensive validation and error handling throughout the processing pipeline

### User Interface
- **Modern Web Interface**: Clean, responsive Streamlit-based UI
- **Interactive Visualizations**: Dynamic charts and graphs using Matplotlib
- **Multi-Page Navigation**: Dedicated views for different analysis types
- **Real-time Processing**: Live feedback during document processing
- **Manual Entry**: Support for manual cash transaction entry

### Technical Features
- **MVC Architecture**: Clean separation of concerns with controllers, services, and models
- **Connection Management**: Optimized database connections for different operation types
- **Comprehensive Testing**: Full test suite covering all major components
- **Modular Design**: Extensible architecture for adding new banks and features
## Testing

The project includes a comprehensive test suite covering all major components:

### Running Tests
```bash
# Run all tests
poe run-tests

# Or run pytest directly
pytest -v Aether_v1/tests/
```

### Test Structure
- **Model Tests**: Unit tests for document processing, table processing, and data processing
- **Service Tests**: Tests for database operations, financial analysis, and plotting services
- **Controller Tests**: Integration tests for business logic controllers
- **Test Data**: Sample bank statements from all supported banks for validation

### Test Coverage
The test suite includes:
- Document processing pipeline validation
- PDF text extraction accuracy testing with real bank statements
- Table reconstruction algorithm verification
- Financial analysis calculation validation
- Database operations and transaction management
- Error handling and edge case coverage

## Project Architecture

The application implements a **Model-View-Controller (MVC) architecture** with a service-oriented design, providing clear separation of concerns and modular extensibility.

### Architecture Overview
```
Frontend (Streamlit Views) 
    ↓ User Interactions
Controllers (Business Logic)
    ↓ Data Operations  
Services (Processing & Analysis)
    ↓ Data Access
Models (Domain Logic & Data Processing)
```
### Key Design Patterns & Principles

1. **MVC Separation**: Clear separation between presentation (Views), business logic (Controllers), and data (Models)

2. **Service-Oriented Architecture**: Business logic encapsulated in reusable services

3. **Factory Pattern**: Bank-specific processing rules selected dynamically based on document analysis

4. **Strategy Pattern**: Different processing strategies for various bank statement formats

5. **Facade Pattern**: Simplified interfaces for complex subsystems (document processing, table processing)

6. **Singleton Pattern**: Centralized resource management (connection manager)

7. **Dependency Injection**: Controllers receive services through dependency injection

### Data Flow Architecture
```
1. PDF Upload (View) 
   ↓
2. File Validation (Controller)
   ↓  
3. Bank Detection (Document Models)
   ↓
4. Text Extraction (Document Models)
   ↓
5. Table Reconstruction (Table Models)
   ↓
6. Data Normalization (Data Models)
   ↓
7. Financial Analysis (Services)
   ↓
8. Visualization Generation (Services)
   ↓
9. Results Display (View)
```

### Benefits of This Architecture
- **Modularity**: Each component has a single responsibility
- **Extensibility**: New banks can be added by implementing new processing strategies
- **Testability**: Each layer can be unit tested independently
- **Maintainability**: Clear separation makes debugging and updates easier
- **Scalability**: Service-oriented design allows for easy scaling of specific components
- **Reusability**: Services and models can be reused across different controllers
## License
This project is licensed under the MIT License.

---

*Aether_v1 - Advanced Financial Statement Analysis Platform*
