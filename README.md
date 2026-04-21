# Aether

**Version 0.1.0** - Initial Release

Aether is a comprehensive financial analysis platform that processes bank statements from multiple Mexican banks. The application features an advanced document processing pipeline with direct PDF text extraction, table reconstruction, and financial analysis capabilities through a modern Streamlit web interface.

This is the initial state of the application, providing core functionality for transaction management and financial analysis.

# Technical Description

Aether is built on a modern MVC architecture with a service-oriented design, featuring advanced PDF processing capabilities, PostgreSQL database integration, and asynchronous operations for optimal performance. The application uses intelligent document analysis to extract transaction data from bank statements and provides comprehensive financial analysis through an intuitive web interface.

## Project Structure

The project follows a modular MVC architecture with clear separation of concerns:

```bash
/Aether_v1
│
├── /config               # Configuration settings and environment variables
├── /constants            # Application constants, enums, and icon definitions
├── /controllers          # MVC Controllers handling business logic and request processing
├── /frontend             # Streamlit web application
│   ├── /assets           # Static files (logos, images)
│   ├── /components       # Reusable UI components and popups
│   └── /views            # Individual page views for each application section
├── /models               # Data models, Pydantic schemas, and business logic entities
│   ├── /validators       # Data validation logic
│   └── /views_data       # View-specific data models
├── /services             # Business logic services and core functionality
│   ├── /database         # Database operations and data access layer
│   └── /statement_data_extraction # PDF processing pipeline and extraction services
├── /tests                # Comprehensive test suite
├── /utils                # Utility functions and helper methods
├── pyproject.toml        # Modern Python project configuration
└── README.md             # Project documentation
```

## Python Versions

The project requires **Python 3.12 or higher** as specified in the `pyproject.toml` configuration.

## Dependencies

### Project Dependencies

Core production dependencies required for the application to run:

- `streamlit==1.51.0` - Web application framework
- `pandas==2.2.3` - Data manipulation and analysis
- `matplotlib==3.10.1` - Data visualization and plotting
- `pdfplumber==0.11.6` - PDF text and coordinate extraction
- `scikit-learn==1.6.1` - Machine learning utilities for data analysis
- `pydantic==2.9.2` - Data validation and settings management
- `psycopg2-binary==2.9.10` - PostgreSQL database adapter
- `python-dotenv==1.1.1` - Environment variable management
- `passlib[argon2]==1.7.4` - Password hashing and authentication
- `openai==2.14.0` - OpenAI API integration

### Dev Optional Dependencies

Development and testing dependencies:

- `poe-the-poet>=0.24.0` - Task runner for development workflows
- `basedpyright==1.36.1` - Static type checker for Python
- `ruff==0.14.9` - Fast Python linter and code formatter

### Test Optional Dependencies

Testing framework:

- `pytest>=7.0.0` - Testing framework

# How to Use It

Aether provides two primary ways to manage your financial transactions:

## 1. Bank Statement Upload

Upload PDF bank statements from supported Mexican banks. The application automatically:
- Detects the bank and statement type (debit/credit)
- Extracts transaction data using intelligent PDF processing
- Identifies potential duplicate transactions using a robust pattern-matching system
- Allows you to review and decide how to handle potential duplicates before importing

## 2. Manual Transaction Entry

Manually add individual transactions through the "Add Transaction" view, allowing you to:
- Enter transactions that may not appear in bank statements
- Categorize transactions immediately
- Add cash transactions or other non-bank transactions
- Use transaction templates for frequently recurring transactions

## Duplicate Detection System

Aether implements a robust duplicate detection system that analyzes transaction patterns including:
- Transaction date and amount
- Description matching
- Bank and statement type
- Time-based proximity analysis

When potential duplicates are detected during statement upload, the system presents them for review, allowing you to decide whether to keep, merge, or skip duplicate entries.

## Running the Application

### Run with streamlit run frontend/app.py

Navigate to the Aether_v1 directory and run the Streamlit application:

```bash
cd Aether_v1
streamlit run frontend/app.py
```

### Run with poe-the-poet

Use the project task runner for development:

```bash
# Run the application
poe run-app

# Run tests
poe run-tests
```

# Views Description

The application provides a comprehensive set of views organized into logical sections based on the Streamlit navigation structure:

## Overview Section

- **Home**: Main dashboard with financial health metrics, savings analysis, and key performance indicators
- **Cards**: Manage and configure your bank cards (debit and credit cards)
- **Goals**: Financial goals management including budgets, savings targets, and debt tracking
- **Add Transaction**: Manual entry of transactions with categorization and template support

## Analytics Section

- **Income Analysis**: Detailed income pattern analysis with trends and forecasting
- **Expenses Analysis**: Comprehensive expense categorization and trend analysis

## Data Section

- **Transactions**: Data export and transaction management interface with filtering and editing capabilities
- **Upload Statements**: PDF statement processing and transaction extraction with duplicate detection

## Account Section

- **Profile**: User profile configuration and settings management
- **Log out**: User session management

# Supported Banks

The application currently supports the following Mexican banks with intelligent format detection:

### Fully Supported Banks

- **Banorte**: Debit and credit cards with legacy and new format support
- **BBVA**: Debit and credit cards with enhanced format support
- **Nu Bank**: Debit and credit cards with account movement tracking
- **Banamex**: Credit cards with legacy and new format support
- **HSBC**: Credit cards with transaction processing and categorization
- **Inbursa**: Debit and credit cards with promotional tracking

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
5. **Singleton Pattern**: Centralized resource management (connection manager)
6. **Dependency Injection**: Controllers receive services through dependency injection

## PostgreSQL Database

The application uses PostgreSQL as its primary database with the following features:

### Database Configuration

- Connection pooling with different pool types for various operations:
  - **Quick Read Pool**: Optimized for fast read operations (2-10 connections)
  - **Session Pool**: For user interactions (1-5 connections)
  - **Batch Pool**: For bulk operations (1-3 connections)
- Environment-based configuration through `.env` file
- Connection management with automatic timeout and memory optimization

### Database Schema Summary

The database includes the following main entities:

- **Users**: User authentication, session management, and user metadata
- **Categories**: Transaction categorization system with predefined groups (Hogar, Transporte, Alimentación, Ocio, Salud, Finanzas, Ingresos, Otros)
- **Transactions**: Core transaction data with date-based partitioning for optimal performance. Supports multiple transaction types (Abono, Cargo, Saldo inicial) and multiple banks
- **Goals**: Financial goals and budget tracking with support for different goal types (Presupuesto, Ahorro, Deuda, Ingresos) and status tracking
- **Templates**: Reusable transaction and goal templates with JSON-based default values
- **Cards**: Bank card management linking cards to users with bank and statement type information

For complete database structure details, including all tables, relationships, and constraints, refer to the `init_db.sql` file.

## Modern Development Tools

Aether leverages modern Python development tools and practices to ensure code quality, performance, and maintainability:

### Type Safety and Validation

- **Pydantic**: Used extensively for data models, providing runtime type validation, serialization, and settings management. All data models use Pydantic schemas for robust data validation.

### Code Quality Tools

- **Basedpyright**: Static type checker configured for Python 3.12, ensuring type safety across the codebase
- **Ruff**: Fast Python linter and code formatter (v0.14.9) configured with strict rules (E, F, I, UP, B) to maintain clean, consistent code

### Performance Optimization

- **Async Functions**: The application implements asynchronous operations for improved performance:
  - **Database Operations**: Async database queries for financial analysis
  - **PDF Processing**: Concurrent processing of multiple PDF files
  - **Data Analysis**: Parallel execution of financial calculations
  - **View Data Loading**: Asynchronous data loading for dashboard components
- Uses `asyncio.TaskGroup()` for concurrent operations
- Async database service methods for optimal I/O performance

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

> [!WARNING]
> Must have a .env file with the host, port, name, user and password for the database, could be local or hosted in some Platform. Check the init_db.sql file to initialize the database with the required Structure

The application requires a `.env` file in the project root with the following database configuration:

```env
IS_SUPABASE=1 or 0 depending on if you are using supabase or just a regular PostgreSQL database
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
- **Supabase** (managed PostgreSQL with additional features)

Use the `init_db.sql` file to initialize the database with the required schema, including:

- User authentication tables
- Transaction storage with date partitioning
- Category management system
- Financial goals tracking
- Template system for reusable configurations
