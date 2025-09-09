#!/usr/bin/env python3
"""
DCF Web Interface
A web-based interface for discounted cash flow analysis with company search functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import requests
from datetime import datetime, timedelta
import warnings
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
warnings.filterwarnings('ignore')

# Import the DCF analyzer class
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the standalone DCF analyzer
try:
    from standalone_dcf_analyzer import StandaloneDCFAnalyzer
except ImportError:
    # Fallback implementation if main analyzer is not available
    class StandaloneDCFAnalyzer:
        def __init__(self, ticker):
            self.ticker = ticker.upper()
            self.risk_free_rate = 0.045
            self.market_risk_premium = 0.06
        
        def calculate_dcf_valuation(self, years=5):
            return None
        
        def generate_investment_recommendation(self, dcf_results):
            return {'recommendation': 'HOLD', 'rationale': 'Analysis not available'}

class DCFWebInterface:
    """
    Web interface for DCF analysis with enhanced features.
    """
    
    def __init__(self):
        self.setup_page_config()
        self.setup_css()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="DCF Valuation Analyzer",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_css(self):
        """Add custom CSS styling."""
        st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
            margin: 0.5rem 0;
        }
        .recommendation-buy {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #28a745;
        }
        .recommendation-sell {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #dc3545;
        }
        .recommendation-hold {
            background-color: #fff3cd;
            color: #856404;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #ffc107;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-left: 20px;
            padding-right: 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1f77b4;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def search_companies(self, query, limit=10):
        """
        Search for companies by name or ticker.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            list: List of company dictionaries
        """
        if not query or len(query) < 2:
            return []
        
        try:
            # Use yfinance to search for tickers
            # This is a simplified approach - in production you might want to use a dedicated API
            search_results = []
            
            # Common tickers to search through
            common_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
                'UNH', 'JNJ', 'V', 'PG', 'JPM', 'MA', 'HD', 'CVX', 'PFE', 'ABBV',
                'BAC', 'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'WMT', 'DHR', 'VZ',
                'ADBE', 'NFLX', 'CRM', 'ACN', 'TXN', 'QCOM', 'NKE', 'MRK', 'ABT',
                'LIN', 'NEE', 'PM', 'T', 'HON', 'UNP', 'LOW', 'SPGI', 'RTX', 'INTU'
            ]
            
            # Search through common tickers
            for ticker in common_tickers:
                if query.upper() in ticker.upper():
                    try:
                        stock = yf.Ticker(ticker)
                        info = stock.info
                        if info and 'longName' in info:
                            search_results.append({
                                'ticker': ticker,
                                'name': info.get('longName', ticker),
                                'sector': info.get('sector', 'N/A'),
                                'market_cap': info.get('marketCap', 0)
                            })
                    except:
                        continue
                
                if len(search_results) >= limit:
                    break
            
            # Also try to get info for the query if it looks like a ticker
            if len(query) <= 5 and query.isalpha():
                try:
                    stock = yf.Ticker(query.upper())
                    info = stock.info
                    if info and 'longName' in info:
                        # Check if not already in results
                        if not any(r['ticker'] == query.upper() for r in search_results):
                            search_results.insert(0, {
                                'ticker': query.upper(),
                                'name': info.get('longName', query.upper()),
                                'sector': info.get('sector', 'N/A'),
                                'market_cap': info.get('marketCap', 0)
                            })
                except:
                    pass
            
            return search_results[:limit]
            
        except Exception as e:
            st.error(f"Error searching companies: {e}")
            return []
    
    def display_company_search(self):
        """Display company search interface."""
        st.markdown('<h1 class="main-header">DCF Valuation Analyzer</h1>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Company search input
            search_query = st.text_input(
                "Search for a company by name or ticker:",
                placeholder="e.g., Apple, AAPL, Microsoft, MSFT...",
                key="company_search"
            )
        
        with col2:
            st.markdown("### Quick Examples")
            if st.button("Apple (AAPL)"):
                st.session_state.selected_company = {'ticker': 'AAPL', 'name': 'Apple Inc.'}
            if st.button("Microsoft (MSFT)"):
                st.session_state.selected_company = {'ticker': 'MSFT', 'name': 'Microsoft Corporation'}
            if st.button("Tesla (TSLA)"):
                st.session_state.selected_company = {'ticker': 'TSLA', 'name': 'Tesla, Inc.'}
        
        # Display search results
        if search_query and len(search_query) >= 2:
            with st.spinner("Searching companies..."):
                search_results = self.search_companies(search_query)
            
            if search_results:
                st.markdown("### Search Results")
                
                for i, company in enumerate(search_results):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**{company['name']}**")
                        st.write(f"*{company['sector']}*")
                    
                    with col2:
                        market_cap = company.get('market_cap', 0)
                        if market_cap > 0:
                            if market_cap >= 1e12:
                                st.write(f"Market Cap: ${market_cap/1e12:.1f}T")
                            elif market_cap >= 1e9:
                                st.write(f"Market Cap: ${market_cap/1e9:.1f}B")
                            else:
                                st.write(f"Market Cap: ${market_cap/1e6:.1f}M")
                        else:
                            st.write("Market Cap: N/A")
                    
                    with col3:
                        if st.button(f"Select", key=f"select_{i}"):
                            st.session_state.selected_company = company
                            st.rerun()
                    
                    st.divider()
            else:
                st.info("No companies found. Try a different search term.")
        
        # Display selected company
        if 'selected_company' in st.session_state:
            company = st.session_state.selected_company
            st.success(f"Selected: **{company['name']}** ({company['ticker']})")
            
            if st.button("Run DCF Analysis", type="primary"):
                return company['ticker']
        
        return None
    
    def display_loading_state(self):
        """Display loading animation."""
        with st.spinner("Running DCF Analysis... This may take a few moments."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress
            for i in range(100):
                progress_bar.progress(i + 1)
                if i < 20:
                    status_text.text("Fetching stock data...")
                elif i < 40:
                    status_text.text("Calculating financial metrics...")
                elif i < 60:
                    status_text.text("Projecting future cash flows...")
                elif i < 80:
                    status_text.text("Computing DCF valuation...")
                else:
                    status_text.text("Generating recommendation...")
                time.sleep(0.05)
            
            progress_bar.empty()
            status_text.empty()
    
    def create_valuation_chart(self, dcf_results):
        """Create valuation comparison chart."""
        if not dcf_results:
            return None
        
        current_price = dcf_results['current_price']
        dcf_value = dcf_results['dcf_value_per_share']
        
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=['Current Price', 'DCF Intrinsic Value'],
            y=[current_price, dcf_value],
            marker_color=['#ff6b6b', '#4ecdc4'],
            text=[f'${current_price:.2f}', f'${dcf_value:.2f}'],
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Stock Valuation Comparison",
            xaxis_title="Valuation Type",
            yaxis_title="Price ($)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_cash_flow_chart(self, projections):
        """Create cash flow projection chart."""
        if projections.empty:
            return None
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=projections['Year'],
            y=projections['Projected_FCF'],
            mode='lines+markers',
            name='Projected FCF',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Projected Free Cash Flow",
            xaxis_title="Year",
            yaxis_title="Free Cash Flow ($)",
            height=400,
            hovermode='x unified'
        )
        
        return fig
    
    def create_wacc_breakdown_chart(self, dcf_results):
        """Create WACC breakdown chart."""
        if not dcf_results:
            return None
        
        # Simplified WACC breakdown visualization
        wacc = dcf_results['wacc']
        risk_free = dcf_results['risk_free_rate']
        beta = dcf_results['beta']
        market_premium = 0.06  # Default market risk premium
        
        cost_of_equity = risk_free + beta * market_premium
        
        fig = go.Figure(data=[
            go.Bar(
                x=['Risk-Free Rate', 'Market Risk Premium', 'Beta Adjustment', 'Total Cost of Equity'],
                y=[risk_free, market_premium, (beta - 1) * market_premium, cost_of_equity],
                marker_color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'],
                text=[f'{risk_free:.1%}', f'{market_premium:.1%}', f'{(beta-1)*market_premium:.1%}', f'{cost_of_equity:.1%}'],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Cost of Equity Breakdown",
            xaxis_title="Component",
            yaxis_title="Rate",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def display_dcf_results(self, dcf_results, recommendation):
        """Display comprehensive DCF analysis results."""
        if not dcf_results:
            st.error("No DCF analysis results available.")
            return
        
        # Header with recommendation
        st.markdown("## DCF Analysis Results")
        
        # Recommendation banner
        rec_class = "recommendation-hold"
        if "BUY" in recommendation['recommendation']:
            rec_class = "recommendation-buy"
        elif "SELL" in recommendation['recommendation']:
            rec_class = "recommendation-sell"
        
        st.markdown(f"""
        <div class="{rec_class}">
            <h3>Investment Recommendation: {recommendation['recommendation']}</h3>
            <p><strong>Rationale:</strong> {recommendation['rationale']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current Price",
                f"${dcf_results['current_price']:.2f}",
                delta=f"{dcf_results['upside_downside_pct']:+.1f}%"
            )
        
        with col2:
            st.metric(
                "DCF Intrinsic Value",
                f"${dcf_results['dcf_value_per_share']:.2f}",
                delta=f"{dcf_results['upside_downside_pct']:+.1f}%"
            )
        
        with col3:
            st.metric(
                "WACC",
                f"{dcf_results['wacc']:.1%}",
                help="Weighted Average Cost of Capital"
            )
        
        with col4:
            st.metric(
                "Beta",
                f"{dcf_results['beta']:.2f}",
                help="Stock's volatility relative to market"
            )
        
        # Tabs for detailed information
        tab1, tab2, tab3, tab4 = st.tabs(["Valuation", "Financials", "Projections", "Assumptions"])
        
        with tab1:
            st.markdown("### Valuation Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Valuation chart
                valuation_chart = self.create_valuation_chart(dcf_results)
                if valuation_chart:
                    st.plotly_chart(valuation_chart, use_container_width=True)
            
            with col2:
                # Valuation details
                st.markdown("#### Valuation Components")
                st.write(f"**Enterprise Value:** ${dcf_results['enterprise_value']:,.0f}")
                st.write(f"**Equity Value:** ${dcf_results['equity_value']:,.0f}")
                st.write(f"**Terminal Value:** ${dcf_results['terminal_value']:,.0f}")
                st.write(f"**PV of Cash Flows:** ${dcf_results['present_value_cash_flows']:,.0f}")
                st.write(f"**PV of Terminal Value:** ${dcf_results['present_value_terminal']:,.0f}")
                st.write(f"**Net Debt:** ${dcf_results['net_debt']:,.0f}")
                st.write(f"**Shares Outstanding:** {dcf_results['shares_outstanding']:,.0f}")
        
        with tab2:
            st.markdown("### Financial Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Company Information")
                st.write(f"**Company:** {dcf_results['company_name']}")
                st.write(f"**Sector:** {dcf_results['sector']}")
                st.write(f"**Market Cap:** ${dcf_results['market_cap']:,.0f}")
                st.write(f"**P/E Ratio:** {dcf_results['pe_ratio']:.2f}")
                st.write(f"**P/B Ratio:** {dcf_results['pb_ratio']:.2f}")
            
            with col2:
                # WACC breakdown chart
                wacc_chart = self.create_wacc_breakdown_chart(dcf_results)
                if wacc_chart:
                    st.plotly_chart(wacc_chart, use_container_width=True)
        
        with tab3:
            st.markdown("### Cash Flow Projections")
            
            if not dcf_results['projections'].empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cash flow chart
                    cash_flow_chart = self.create_cash_flow_chart(dcf_results['projections'])
                    if cash_flow_chart:
                        st.plotly_chart(cash_flow_chart, use_container_width=True)
                
                with col2:
                    # Projections table
                    st.markdown("#### Projected Cash Flows")
                    projections_df = dcf_results['projections'].copy()
                    projections_df['Growth_Rate'] = projections_df['Growth_Rate'].apply(lambda x: f"{x:.1%}")
                    projections_df['Projected_FCF'] = projections_df['Projected_FCF'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(projections_df, use_container_width=True)
            else:
                st.info("No cash flow projections available.")
        
        with tab4:
            st.markdown("### DCF Assumptions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Key Assumptions")
                st.write(f"**Risk-Free Rate:** {dcf_results['risk_free_rate']:.2%}")
                st.write(f"**Market Risk Premium:** 6.0%")
                st.write(f"**Beta:** {dcf_results['beta']:.2f}")
                st.write(f"**WACC:** {dcf_results['wacc']:.2%}")
                st.write(f"**Terminal Growth Rate:** 3.0%")
                st.write(f"**Projection Period:** 5 years")
            
            with col2:
                st.markdown("#### Analysis Details")
                st.write(f"**Analysis Date:** {dcf_results['analysis_date']}")
                st.write(f"**Data Source:** Yahoo Finance")
                st.write(f"**Methodology:** Discounted Cash Flow")
                st.write(f"**Terminal Value Method:** Gordon Growth Model")
        
        # Footer
        st.markdown("---")
        st.markdown("### Disclaimer")
        st.markdown("""
        This analysis is for educational and informational purposes only. It should not be considered as financial advice. 
        Always conduct your own research and consult with a qualified financial advisor before making investment decisions.
        """)
    
    def run(self):
        """Main application loop."""
        # Sidebar
        with st.sidebar:
            st.markdown("## DCF Analyzer")
            st.markdown("### Features:")
            st.markdown("• Real-time financial data")
            st.markdown("• DCF intrinsic valuation")
            st.markdown("• Buy/Sell/Hold recommendations")
            st.markdown("• Interactive visualizations")
            st.markdown("• Comprehensive analysis")
            
            st.markdown("---")
            st.markdown("### How it works:")
            st.markdown("1. Search for a company")
            st.markdown("2. Select from results")
            st.markdown("3. Run DCF analysis")
            st.markdown("4. Review recommendations")
            
            st.markdown("---")
            st.markdown("### Important Notes:")
            st.markdown("• Analysis may take 30-60 seconds")
            st.markdown("• Results are estimates only")
            st.markdown("• Not financial advice")
        
        # Main content
        ticker = self.display_company_search()
        
        if ticker:
            # Run DCF analysis
            self.display_loading_state()
            
            try:
                # Initialize analyzer
                analyzer = StandaloneDCFAnalyzer(ticker)
                
                # Run analysis
                dcf_results = analyzer.calculate_dcf_valuation(years=5)
                
                if dcf_results:
                    # Generate recommendation
                    recommendation = analyzer.generate_investment_recommendation(dcf_results)
                    
                    # Display results
                    self.display_dcf_results(dcf_results, recommendation)
                    
                    # Success message
                    st.success("Analysis completed successfully!")
                    
                else:
                    st.error("Analysis failed. Please try again with a different ticker.")
                    
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.info("Please try again or contact support if the issue persists.")


def main():
    """Main function to run the web interface."""
    app = DCFWebInterface()
    app.run()


if __name__ == "__main__":
    main()
