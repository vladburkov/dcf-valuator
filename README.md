# DCF Valuation Analyzer

A comprehensive web-based application for performing Discounted Cash Flow (DCF) analysis on publicly traded companies. This tool provides professional-grade financial modeling capabilities with real-time data integration and investment recommendations.

## Overview

The DCF Valuation Analyzer is designed for financial analysts, investors, and students who need to perform fundamental analysis on stocks. It combines modern web technologies with robust financial modeling to deliver accurate valuations and actionable investment insights.

## Features

### Core Functionality
- **Real-time Financial Data**: Integrates with Yahoo Finance API for current market data
- **DCF Modeling**: Implements industry-standard discounted cash flow methodology
- **Investment Recommendations**: Generates buy/sell/hold recommendations based on valuation analysis
- **Interactive Visualizations**: Charts and graphs for better data interpretation
- **Company Search**: Autocomplete functionality for easy company selection

### Technical Capabilities
- **Rate Limiting Handling**: Robust error handling and retry mechanisms for API reliability
- **Financial Calculations**: WACC, beta calculation, cash flow projections, and terminal value modeling
- **Data Validation**: Comprehensive data quality checks and fallback mechanisms
- **Responsive Design**: Modern web interface that works across devices

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   # Ensure you have the following files in your directory:
   # - dcf_web_interface.py
   # - standalone_dcf_analyzer.py
   # - requirements_web.txt
   # - launch_dcf_web.py
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements_web.txt
   ```

3. **Launch the application**
   ```bash
   python launch_dcf_web.py
   ```

   Or run directly with Streamlit:
   ```bash
   streamlit run dcf_web_interface.py --server.port 8502
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:8502`
   - The interface will load automatically

## Usage

### Basic Workflow

1. **Search for a Company**
   - Enter a company name or ticker symbol in the search box
   - Use the autocomplete suggestions or quick example buttons
   - Select your desired company from the results

2. **Run Analysis**
   - Click "Run DCF Analysis" to begin the valuation process
   - Wait for the analysis to complete (typically 30-60 seconds)
   - Review the comprehensive results

3. **Interpret Results**
   - Review the investment recommendation (Buy/Sell/Hold)
   - Examine the DCF intrinsic value vs. current market price
   - Analyze the financial metrics and assumptions
   - Study the cash flow projections and growth rates

### Understanding the Output

#### Investment Recommendation
- **Strong Buy**: DCF value significantly exceeds current price (>20% upside)
- **Buy**: Attractive upside potential (10-20% upside)
- **Hold**: Fair value range (-5% to +10% variance)
- **Sell**: Overvalued with downside risk (-5% to -15%)
- **Strong Sell**: Significantly overvalued (>15% downside)

#### Key Metrics
- **DCF Intrinsic Value**: Calculated fair value per share
- **WACC**: Weighted Average Cost of Capital used for discounting
- **Beta**: Stock's volatility relative to the market
- **Terminal Value**: Long-term value beyond projection period

## Methodology

### DCF Model Components

1. **Free Cash Flow Calculation**
   - Operating Cash Flow minus Capital Expenditures
   - Historical analysis with trend identification
   - Growth rate estimation from historical data

2. **WACC Calculation**
   - Cost of Equity: Risk-free rate + Beta × Market Risk Premium
   - Cost of Debt: Risk-free rate + Credit spread
   - Weighted average based on capital structure

3. **Cash Flow Projections**
   - 5-year forward-looking projections
   - Declining growth rate methodology
   - Terminal value using Gordon Growth Model

4. **Valuation Framework**
   - Present value of projected cash flows
   - Terminal value calculation
   - Enterprise value to equity value conversion

### Assumptions

- **Risk-free Rate**: 10-year Treasury yield (updated daily)
- **Market Risk Premium**: 6.0% (historical average)
- **Terminal Growth Rate**: 3.0% (long-term GDP growth)
- **Projection Period**: 5 years
- **Tax Rate**: 25% (corporate average)

## Technical Architecture

### Backend Components
- **StandaloneDCFAnalyzer**: Core financial modeling engine
- **Data Integration**: Yahoo Finance API with retry mechanisms
- **Calculation Engine**: NumPy and Pandas for financial computations
- **Error Handling**: Comprehensive exception management

### Frontend Components
- **Streamlit Framework**: Modern web application framework
- **Interactive Charts**: Plotly for data visualization
- **Responsive Design**: CSS styling for professional appearance
- **User Experience**: Intuitive interface with loading states

### Data Sources
- **Yahoo Finance**: Primary data provider for financial statements and market data
- **Treasury Data**: Risk-free rate from government bond yields
- **Market Data**: Real-time stock prices and company information

## Limitations and Disclaimers

### Data Limitations
- Analysis depends on the quality and availability of financial data
- Historical data may not predict future performance
- Market conditions can change rapidly

### Model Limitations
- DCF models are sensitive to assumptions and projections
- Terminal value calculations involve significant uncertainty
- Growth rate estimates are based on historical trends

### Investment Disclaimer
**This tool is for educational and informational purposes only. It should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.**

## Troubleshooting

### Common Issues

1. **Application won't start**
   - Ensure all dependencies are installed: `pip install -r requirements_web.txt`
   - Check Python version compatibility (3.8+)
   - Verify port availability (8502)

2. **Data fetch errors**
   - Check internet connection
   - Wait and retry (rate limiting may be in effect)
   - Try a different ticker symbol

3. **Analysis fails**
   - Ensure the company has sufficient financial data
   - Try companies with longer trading history
   - Check if the ticker symbol is correct

### Performance Optimization
- Analysis typically takes 30-60 seconds
- Larger companies with more data may take longer
- Rate limiting is built-in to prevent API overuse

## Contributing

This is a standalone financial analysis tool. For modifications or enhancements:

1. Review the code structure and methodology
2. Test changes with multiple companies
3. Ensure financial calculations remain accurate
4. Maintain the professional user interface

## License

This project is provided as-is for educational and research purposes. Users are responsible for compliance with data provider terms of service and applicable regulations.

## Contact

For technical issues or questions about the methodology, please review the code documentation and financial modeling best practices.

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Compatibility**: Python 3.8+, Modern Web Browsers