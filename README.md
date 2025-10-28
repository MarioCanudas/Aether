# Aether_v1

Aether_v1 is a comprehensive financial analysis platform that processes bank statements from multiple Mexican banks. The application features an advanced document processing pipeline with direct PDF text extraction, table reconstruction, and financial analysis capabilities through a modern Streamlit web interface. It supports **Banorte**, **BBVA**, **Nu Bank**, **Banamex**, **HSBC**, and **Inbursa** statements across both debit and credit card formats, with intelligent text processing and automated transaction categorization.

# Technical Description

Aether_v1 is built on a modern MVC architecture with a service-oriented design, featuring advanced PDF processing capabilities, PostgreSQL database integration, and asynchronous operations for optimal performance. The application uses intelligent document analysis to extract transaction data from bank statements and provides comprehensive financial analysis through an intuitive web interface.

## Project Structure

The project follows a modular MVC architecture with clear separation of concerns:

```bash
/Aether_v1
│
├── /config               # Configuration settings and constants
├── /controllers          # MVC Controllers for business logic
│   ├── analysis_controller.py      # Financial analysis operations
│   ├── base_controller.py          # Base controller with database scoping
│   ├── cash_transaction_controller.py # Manual transaction entry
│   ├── data_view_controller.py    # Data visualization and export
│   ├── goals_controller.py        # Financial goals management
│   ├── home_controller.py         # Dashboard and overview
│   ├── logs_controller.py         # System logs and monitoring
│   ├── upload_statements_controller.py # PDF processing
│   └── user_configuration_controller.py # User settings
├── /constants            # Application constants and enums
│   ├── banks_properties.py        # Bank-specific configurations
│   ├── dates.py                   # Date handling utilities
│   ├── formats.py                 # Data format definitions
│   └── views_icons.py             # UI icon definitions
├── /frontend             # Streamlit web application
│   ├── /assets           # Static files (logos, images)
│   ├── /components       # Reusable UI components
│   ├── /views            # Individual page views
│   └── app.py            # Main Streamlit application entry point
├── /models               # Data models and business logic
│   ├── /views_data       # View-specific data models
│   ├── amounts.py        # Financial amount handling
│   ├── bank_properties.py # Bank configuration models
│   ├── categories.py     # Transaction categorization
│   ├── financial.py      # Financial calculations
│   ├── goals.py         # Financial goals models
│   └── tables.py        # Data table models
├── /services            # Business logic services
│   ├── /database        # Database operations
│   ├── /statement_data_extraction # PDF processing pipeline
│   ├── connection_management_service.py # Database connection pooling
│   ├── data_processing_service.py # Data processing operations
│   ├── financial_analysis_service.py # Financial analysis calculations
│   ├── plotting_service.py # Chart and visualization generation
│   └── user_session_service.py # User session management
├── /tests               # Comprehensive test suite
├── /utils               # Utility functions and helpers
├── pyproject.toml      # Modern Python project configuration
├── requirements.txt     # Production dependencies
└── README.md           # Project documentation
```

## Python Versions

The project requires **Python 3.9+** as specified in the `pyproject.toml` configuration.

## Dependencies

### Project Dependencies

Core production dependencies required for the application to run:

- `streamlit==1.46.1` - Web application framework
- `pandas==2.2.3` - Data manipulation and analysis
- `matplotlib==3.10.1` - Data visualization and plotting
- `pdfplumber==0.11.6` - PDF text and coordinate extraction
- `scikit-learn==1.6.1` - Machine learning utilities for data analysis
- `pydantic==2.9.2` - Data validation and settings management
- `psycopg2-binary==2.9.10` - PostgreSQL database adapter
- `python-dotenv==1.1.1` - Environment variable management
- `altair==5.5.0` - Statistical visualization library

### Dev Optional Dependencies

Development and testing dependencies:

- `poe-the-poet>=0.24.0` - Task runner for development workflows
- `pytest>=7.0.0` - Testing framework

# How to Use It

## Run with streamlit run frontend/app.py being in Aether_v1/ directory

Navigate to the Aether_v1 directory and run the Streamlit application:

```bash
cd Aether_v1
streamlit run frontend/app.py
```

## Run with poe-the-poet

Use the project task runner for development:

```bash
# Run the application
poe run-app

# Run tests
poe run-tests
```

# Views Description

The application provides a comprehensive set of views organized into logical sections:

## Overview Section
- **Home**: Main dashboard with financial health metrics, savings analysis, and key performance indicators
- **Cash Transaction**: Manual entry of cash transactions with categorization
- **Goals**: Financial goals management including budgets, savings targets, and debt tracking

## Analytics Section
- **Income Analysis**: Detailed income pattern analysis with trends and forecasting
- **Expenses Analysis**: Comprehensive expense categorization and trend analysis

## Data Section
- **Transactions**: Data export and transaction management interface
- **Upload Statements**: PDF statement processing and transaction extraction

## Account Section
- **Log out**: User session management

## Dev Tools Section
- **Users Configuration**: Administrative tools for user management

# Supported Banks

The application currently supports the following Mexican banks with intelligent format detection:

### Fully Supported Banks
- **Banorte**: Debit and credit cards with legacy and new format support
- **BBVA**: Debit and credit cards with enhanced format support (2024+)
- **Nu Bank**: Debit and credit cards with account movement tracking
- **Banamex**: Credit cards with legacy and new format support
- **HSBC**: Credit cards with transaction processing and categorization
- **Inbursa**: Debit and credit cards with promotional tracking

### Banks in Development
- **American Express (AMEX)**: Basic structure implemented
- **Santander**: Bank properties being configured

Each supported bank's statements are processed using specific extraction rules that handle:
- Date format variations (DD/MM/YY, DD-MMM-YYYY, etc.)
- Amount parsing with currency symbols and signs
- Transaction categorization (income vs. expenses)
- Balance calculations and verification
- Period detection and year inference

# Technical Aspects

## Architecture Project (MVC + Services Layer)

The application implements a **Model-View-Controller (MVC) architecture** with a service-oriented design, providing clear separation of concerns and modular extensibility.

### Key Design Patterns & Principles

1. **MVC Separation**: Clear separation between presentation (Views), business logic (Controllers), and data (Models)
2. **Service-Oriented Architecture**: Business logic encapsulated in reusable services
3. **Factory Pattern**: Bank-specific processing rules selected dynamically based on document analysis
4. **Strategy Pattern**: Different processing strategies for various bank statement formats
6. **Singleton Pattern**: Centralized resource management (connection manager)
7. **Dependency Injection**: Controllers receive services through dependency injection

## Postgres DB

The application uses PostgreSQL as its primary database with the following features:

### Database Configuration
- Connection pooling with different pool types for various operations:
  - **Quick Read Pool**: Optimized for fast read operations (2-10 connections)
  - **Session Pool**: For user interactions (1-5 connections)
  - **Batch Pool**: For bulk operations (1-3 connections)
- Environment-based configuration through `.env` file
- Connection management with automatic timeout and memory optimization

### Database Schema
The database includes the following main entities:
- **Users**: User authentication and session management
- **Categories**: Transaction categorization system
- **Transactions**: Core transaction data with partitioning by date
- **Goals**: Financial goals and budget tracking
- **Templates**: Reusable transaction and goal templates

## Async

The application implements asynchronous operations for improved performance:

### Async Implementation Areas
- **Database Operations**: Async database queries for financial analysis
- **PDF Processing**: Concurrent processing of multiple PDF files
- **Data Analysis**: Parallel execution of financial calculations
- **View Data Loading**: Asynchronous data loading for dashboard components

### Key Async Features
- `asyncio.TaskGroup()` for concurrent operations
- Async database service methods
- Concurrent financial analysis calculations

## Extraction Transactions Models from PDF Statements from the Banks

The application features a sophisticated PDF processing pipeline:

### Document Processing Pipeline
1. **PDF Reading**: Uses `pdfplumber` for text and coordinate extraction
2. **Bank Detection**: Automatic bank identification from document content
3. **Text Processing**: Advanced text correction and normalization
4. **Table Reconstruction**: Intelligent table detection and reconstruction
5. **Data Normalization**: Standardized data format conversion
6. **Transaction Extraction**: Final transaction data extraction

### Processing Components
- **`PDFReader`**: Core PDF text extraction
- **`DefaultDocumentAnalyzer`**: Bank detection and document analysis
- **`DefaultTextProcessor`**: Text correction and normalization
- **`TableReconstructor`**: Table reconstruction from extracted data
- **`DefaultTableNormalizer`**: Data normalization and standardization

# Disclaimers

## Must have a .env file with the host, port, name, user and password for the database, could be local or hosted in some Platform. Check the init_db.sql file to initialize the database with the required Structure

The application requires a `.env` file in the project root with the following database configuration:

```env
DB_HOST=your_database_host
DB_PORT=your_database_port
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

The database can be:
- **Local PostgreSQL instance**
- **Cloud-hosted PostgreSQL** (AWS RDS, Google Cloud SQL, Azure Database, etc.)
- **Containerized PostgreSQL** (Docker, etc.)

Use the `init_db.sql` file to initialize the database with the required schema, including:
- User authentication tables
- Transaction storage with date partitioning
- Category management system
- Financial goals tracking
- Template system for reusable configurations

## The user can use the manual transaction input or the statement extraction transaction input, but right now the app cannot delete the duplicates from these types of transaction inputs

**Important Limitation**: The application currently supports two transaction input methods:

1. **Manual Transaction Input**: Users can manually enter cash transactions through the "Cash Transaction" view
2. **Statement Extraction**: Users can upload PDF bank statements for automatic transaction extraction

However, the application **does not currently have duplicate detection or removal functionality**. Users should be aware that:
- Manual transactions and extracted transactions may create duplicates
- No automatic deduplication is performed
- Users should manually review and manage potential duplicate entries
- This limitation may be addressed in future versions

---

*Aether_v1 - Advanced Financial Statement Analysis Platform*