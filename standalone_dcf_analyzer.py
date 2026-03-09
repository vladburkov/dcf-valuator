"""
Standalone DCF Analysis Tool
Complete DCF valuation with buy/sell/hold recommendations.
This is a single-file version that includes everything needed.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import time
import requests
from datetime import datetime, timedelta
import warnings
import threading
warnings.filterwarnings('ignore')


class RateLimiter:
    """
    Global rate limiter to prevent API rate limiting across all instances.
    """
    _lock = threading.Lock()
    _last_request_time = 0
    _min_delay_between_requests = 3.0  # Minimum 3 seconds between any requests
    _rate_limit_detected = False
    _rate_limit_wait_until = 0
    
    @classmethod
    def wait_if_needed(cls):
        """Wait if needed to respect rate limits."""
        with cls._lock:
            current_time = time.time()
            
            # If we've detected rate limiting, wait longer
            if cls._rate_limit_detected and current_time < cls._rate_limit_wait_until:
                wait_time = cls._rate_limit_wait_until - current_time
                if wait_time > 0:
                    print(f" Rate limit active. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    cls._rate_limit_detected = False
            
            # Normal rate limiting - ensure minimum delay between requests
            time_since_last = current_time - cls._last_request_time
            if time_since_last < cls._min_delay_between_requests:
                wait_time = cls._min_delay_between_requests - time_since_last
                time.sleep(wait_time)
            
            cls._last_request_time = time.time()
    
    @classmethod
    def mark_rate_limit(cls, wait_seconds=300):
        """Mark that rate limiting was detected and wait longer."""
        with cls._lock:
            cls._rate_limit_detected = True
            cls._rate_limit_wait_until = time.time() + wait_seconds
            print(f" Rate limit detected. Will wait {wait_seconds} seconds before next request.")
    
    @classmethod
    def reset(cls):
        """Reset rate limiter state."""
        with cls._lock:
            cls._rate_limit_detected = False
            cls._rate_limit_wait_until = 0


class StandaloneDCFAnalyzer:
    """
    Standalone DCF analyzer that handles rate limiting and provides comprehensive analysis.
    """
    
    def __init__(self, ticker):
        """
        Initialize the DCF analyzer for a given ticker.
        
        Args:
            ticker (str): Stock ticker symbol
        """
        self.ticker = ticker.upper()
        self.data = {}
        self.risk_free_rate = 0.045  # Default 4.5%
        self.market_risk_premium = 0.06  # Default 6%
        
    def _is_rate_limit_error(self, error):
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "throttled",
            "quota exceeded",
            "request limit"
        ]
        return any(indicator in error_str for indicator in rate_limit_indicators)
    
    def get_stock_data_with_retry(self, max_retries=3, delay=60):
        """
        Get stock data with enhanced retry logic to handle severe rate limiting.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            delay (int): Base delay between retries in seconds
            
        Returns:
            dict: Stock data or None if failed
        """
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}: Fetching data for {self.ticker}...")
                
                # Use rate limiter before making any request
                RateLimiter.wait_if_needed()
                
                # Much longer delays for retries
                if attempt > 0:
                    # Exponential backoff: 60s, 180s, 540s for attempts 1, 2, 3
                    wait_time = delay * (3 ** attempt) + np.random.uniform(30, 60)
                    print(f"⏳ Waiting {wait_time:.1f} seconds before retry...")
                    time.sleep(wait_time)
                    RateLimiter.wait_if_needed()
                
                # Add initial delay for first attempt
                if attempt == 0:
                    time.sleep(5)  # Initial delay
                    RateLimiter.wait_if_needed()
                
                stock = yf.Ticker(self.ticker)
                
                # Get basic info with timeout
                try:
                    RateLimiter.wait_if_needed()
                    info = stock.info
                    if not info or len(info) < 10:  # Check if we got meaningful data
                        raise Exception("Insufficient info data received")
                except Exception as e:
                    error_msg = str(e)
                    print(f"Info fetch failed: {error_msg}")
                    
                    # Check for rate limiting
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300 + (attempt * 60))
                        if attempt < max_retries - 1:
                            continue
                        else:
                            raise e
                    
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise e
                
                # Get financial statements with individual error handling
                financials = pd.DataFrame()
                balance_sheet = pd.DataFrame()
                cashflow = pd.DataFrame()
                hist = pd.DataFrame()
                
                # Try to get financials with delays
                try:
                    print("Fetching financial statements...")
                    RateLimiter.wait_if_needed()
                    financials = stock.financials
                except Exception as e:
                    error_msg = str(e)
                    print(f" Financials fetch failed: {error_msg}")
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300)
                
                try:
                    RateLimiter.wait_if_needed()
                    balance_sheet = stock.balance_sheet
                except Exception as e:
                    error_msg = str(e)
                    print(f" Balance sheet fetch failed: {error_msg}")
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300)
                
                try:
                    RateLimiter.wait_if_needed()
                    cashflow = stock.cashflow
                except Exception as e:
                    error_msg = str(e)
                    print(f" Cash flow fetch failed: {error_msg}")
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300)
                
                # Get historical data
                try:
                    print("Fetching historical data...")
                    RateLimiter.wait_if_needed()
                    hist = stock.history(period="5y")
                except Exception as e:
                    error_msg = str(e)
                    print(f" Historical data fetch failed: {error_msg}")
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300)
                
                # Get current price with fallback
                current_price = 0
                try:
                    current_price = info.get('currentPrice', 0)
                    if current_price == 0 and not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    elif current_price == 0:
                        # Try to get price from regularMarketPrice
                        current_price = info.get('regularMarketPrice', 0)
                except Exception as e:
                    print(f" Price fetch failed: {e}")
                
                # Calculate beta from historical data
                beta = self._calculate_beta(hist)
                
                stock_data = {
                    'info': info,
                    'financials': financials,
                    'balance_sheet': balance_sheet,
                    'cashflow': cashflow,
                    'historical': hist,
                    'current_price': current_price,
                    'beta': beta
                }
                
                print(f"Successfully fetched data for {self.ticker}")
                return stock_data
                
            except Exception as e:
                error_msg = str(e)
                print(f"Attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a rate limiting error
                if self._is_rate_limit_error(e):
                    RateLimiter.mark_rate_limit(wait_seconds=300 + (attempt * 120))
                    if attempt < max_retries - 1:
                        # Wait longer for rate limits
                        wait_time = 300 + (attempt * 120) + np.random.uniform(30, 60)
                        print(f"Rate limited. Waiting {wait_time:.1f} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"All attempts failed for {self.ticker} due to rate limiting")
                        return None
                
                if attempt == max_retries - 1:
                    print(f"All attempts failed for {self.ticker}")
                    return None
                
                # Regular retry delay
                wait_time = delay * (attempt + 1) + np.random.uniform(10, 20)
                print(f"⏳ Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
        
        return None
    
    def _get_minimal_stock_data(self):
        """
        Fallback method to get minimal stock data when rate limiting is severe.
        
        Returns:
            dict: Minimal stock data or None if failed
        """
        try:
            print("🔄 Trying fallback data collection method...")
            
            # Wait longer before trying fallback and use rate limiter
            time.sleep(15)
            RateLimiter.wait_if_needed()
            
            stock = yf.Ticker(self.ticker)
            
            # Try to get just the basic info with rate limiting
            RateLimiter.wait_if_needed()
            info = stock.info
            
            if not info or len(info) < 5:
                print("❌ Fallback method also failed - insufficient data")
                return None
            
            # Get minimal data
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            market_cap = info.get('marketCap', 0)
            shares_outstanding = info.get('sharesOutstanding', 1)
            beta = info.get('beta', 1.0)
            
            # Create minimal stock data
            stock_data = {
                'info': info,
                'financials': pd.DataFrame(),
                'balance_sheet': pd.DataFrame(),
                'cashflow': pd.DataFrame(),
                'historical': pd.DataFrame(),
                'current_price': current_price,
                'beta': beta
            }
            
            print("✅ Fallback method succeeded with minimal data")
            return stock_data
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Fallback method failed: {error_msg}")
            if self._is_rate_limit_error(e):
                RateLimiter.mark_rate_limit(wait_seconds=600)
            return None
    
    def _calculate_beta(self, hist_data):
        """
        Calculate beta using historical stock data vs S&P 500 with retry logic.
        
        Args:
            hist_data: Historical stock price data
            
        Returns:
            float: Beta coefficient
        """
        try:
            if hist_data.empty:
                return 1.0
            
            # Get S&P 500 data for comparison with retry
            max_retries = 3
            sp500_hist = pd.DataFrame()
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        wait_time = 10 * (attempt + 1) + np.random.uniform(5, 10)
                        print(f"⏳ Waiting {wait_time:.1f} seconds before retrying S&P 500 data...")
                        time.sleep(wait_time)
                    
                    RateLimiter.wait_if_needed()
                    sp500 = yf.Ticker("^GSPC")
                    sp500_hist = sp500.history(period="5y")
                    
                    if not sp500_hist.empty:
                        break
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f" S&P 500 data fetch attempt {attempt + 1} failed: {error_msg}")
                    if self._is_rate_limit_error(e):
                        RateLimiter.mark_rate_limit(wait_seconds=300)
                    if attempt == max_retries - 1:
                        print("Using default beta: 1.0")
                        return 1.0
            
            if sp500_hist.empty:
                return 1.0
            
            # Align dates
            common_dates = hist_data.index.intersection(sp500_hist.index)
            if len(common_dates) < 30:  # Need at least 30 days of data
                return 1.0
            
            stock_returns = hist_data.loc[common_dates, 'Close'].pct_change().dropna()
            sp500_returns = sp500_hist.loc[common_dates, 'Close'].pct_change().dropna()
            
            if len(stock_returns) < 10 or len(sp500_returns) < 10:
                return 1.0
            
            # Calculate beta
            covariance = np.cov(stock_returns, sp500_returns)[0][1]
            variance = np.var(sp500_returns)
            beta = covariance / variance if variance != 0 else 1.0
            
            return round(beta, 3)
            
        except Exception as e:
            print(f"Error calculating beta: {e}")
            return 1.0
    
    def get_risk_free_rate(self):
        """
        Get risk-free rate (10-Year Treasury yield) with retry logic.
        
        Returns:
            float: Risk-free rate
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 10 * (attempt + 1) + np.random.uniform(5, 10)
                    print(f"⏳ Waiting {wait_time:.1f} seconds before retrying Treasury yield...")
                    time.sleep(wait_time)
                
                RateLimiter.wait_if_needed()
                print("Fetching 10-year Treasury yield...")
                treasury = yf.Ticker("^TNX")
                treasury_hist = treasury.history(period="1d")
                
                if not treasury_hist.empty:
                    rate = treasury_hist['Close'].iloc[-1] / 100
                    self.risk_free_rate = rate
                    print(f" Risk-free rate: {rate:.2%}")
                    return rate
                else:
                    print("No Treasury data received, using default")
                    break
                    
            except Exception as e:
                error_msg = str(e)
                print(f" Treasury yield fetch attempt {attempt + 1} failed: {error_msg}")
                if self._is_rate_limit_error(e):
                    RateLimiter.mark_rate_limit(wait_seconds=300)
                if attempt == max_retries - 1:
                    print("Using default risk-free rate: 4.5%")
                    return self.risk_free_rate
        
        print("Using default risk-free rate: 4.5%")
        return self.risk_free_rate
    
    def calculate_wacc(self, stock_data):
        """
        Calculate Weighted Average Cost of Capital (WACC).
        
        Args:
            stock_data: Stock data dictionary
            
        Returns:
            float: WACC
        """
        try:
            info = stock_data['info']
            
            # Get risk-free rate
            risk_free_rate = self.get_risk_free_rate()
            
            # Calculate cost of equity using CAPM
            beta = stock_data['beta']
            cost_of_equity = risk_free_rate + beta * self.market_risk_premium
            
            # Get market cap and debt
            market_cap = info.get('marketCap', 0)
            total_debt = info.get('totalDebt', 0)
            total_cash = info.get('totalCash', 0)
            net_debt = total_debt - total_cash
            
            # Estimate cost of debt
            cost_of_debt = risk_free_rate + 0.03  # 3% spread
            
            # Calculate weights
            total_capital = market_cap + net_debt
            if total_capital == 0:
                return cost_of_equity
            
            equity_weight = market_cap / total_capital
            debt_weight = net_debt / total_capital
            
            # Calculate WACC
            tax_rate = 0.25  # 25% tax rate
            wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
            
            print(f"WACC calculated: {wacc:.2%}")
            return wacc
            
        except Exception as e:
            print(f"Error calculating WACC: {e}")
            return 0.10  # Default 10%
    
    def calculate_free_cash_flow(self, stock_data):
        """
        Calculate Free Cash Flow from available data.
        
        Args:
            stock_data: Stock data dictionary
            
        Returns:
            pd.DataFrame: Historical free cash flow data
        """
        try:
            cashflow = stock_data['cashflow']
            
            if cashflow.empty:
                print("No cash flow data available")
                return pd.DataFrame()
            
            # Extract operating cash flow and capital expenditures
            operating_cf = None
            capex = None
            
            # Try different possible names for operating cash flow
            for name in ['Total Cash From Operating Activities', 'Operating Cash Flow', 'Net Cash From Operating Activities']:
                if name in cashflow.index:
                    operating_cf = cashflow.loc[name]
                    break
            
            # Try different possible names for capital expenditures
            for name in ['Capital Expenditures', 'Capital Expenditure', 'Payments To Acquire Property Plant And Equipment']:
                if name in cashflow.index:
                    capex = cashflow.loc[name]
                    break
            
            if operating_cf is None:
                print("Operating cash flow data not found")
                return pd.DataFrame()
            
            if capex is None:
                print("Capital expenditure data not found, using 0")
                capex = pd.Series([0] * len(operating_cf), index=operating_cf.index)
            
            # Calculate Free Cash Flow
            free_cash_flow = operating_cf - capex
            
            fcf_df = pd.DataFrame({
                'Operating Cash Flow': operating_cf,
                'Capital Expenditures': capex,
                'Free Cash Flow': free_cash_flow
            })
            
            print("Free Cash Flow calculated")
            return fcf_df
            
        except Exception as e:
            print(f"Error calculating Free Cash Flow: {e}")
            return pd.DataFrame()
    
    def _estimate_free_cash_flow(self, stock_data):
        """
        Estimate free cash flow when actual data is not available.
        
        Args:
            stock_data: Stock data dictionary
            
        Returns:
            pd.DataFrame: Estimated free cash flow data
        """
        try:
            info = stock_data['info']
            
            # Try to get revenue and net income from info
            revenue = info.get('totalRevenue', 0)
            net_income = info.get('netIncomeToCommon', 0)
            
            if revenue == 0 and net_income == 0:
                print("Cannot estimate FCF without revenue or net income data")
                return pd.DataFrame()
            
            # Estimate FCF as a percentage of revenue or net income
            if revenue > 0:
                # Assume FCF is 10-15% of revenue for most companies
                estimated_fcf = revenue * 0.12
            else:
                # Assume FCF is 80-120% of net income
                estimated_fcf = net_income * 1.0
            
            # Create a simple FCF series for the last 3 years
            fcf_series = pd.Series([estimated_fcf * 0.9, estimated_fcf * 0.95, estimated_fcf], 
                                 index=pd.date_range(end='2024-12-31', periods=3, freq='Y'))
            
            fcf_df = pd.DataFrame({
                'Operating Cash Flow': fcf_series * 1.2,  # Estimate OCF as 120% of FCF
                'Capital Expenditures': fcf_series * 0.2,  # Estimate CapEx as 20% of FCF
                'Free Cash Flow': fcf_series
            })
            
            print(" Estimated free cash flow from available data")
            return fcf_df
            
        except Exception as e:
            print(f"Error estimating free cash flow: {e}")
            return pd.DataFrame()
    
    def project_future_cash_flows(self, fcf_data, years=5):
        """
        Project future free cash flows based on historical data.
        
        Args:
            fcf_data: Historical FCF data
            years: Number of years to project
            
        Returns:
            pd.DataFrame: Projected cash flows
        """
        try:
            if fcf_data.empty:
                print("No FCF data available for projection")
                return pd.DataFrame()
            
            # Get latest FCF
            latest_fcf = fcf_data['Free Cash Flow'].iloc[0]
            
            if pd.isna(latest_fcf) or latest_fcf == 0:
                print("Invalid latest FCF value")
                return pd.DataFrame()
            
            # Calculate growth rate from historical data
            fcf_values = fcf_data['Free Cash Flow'].dropna()
            if len(fcf_values) < 2:
                growth_rate = 0.05  # Default 5% growth
            else:
                # Calculate average growth rate
                growth_rates = []
                for i in range(1, len(fcf_values)):
                    if fcf_values.iloc[i-1] != 0:
                        growth = (fcf_values.iloc[i] - fcf_values.iloc[i-1]) / abs(fcf_values.iloc[i-1])
                        growth_rates.append(growth)
                
                if growth_rates:
                    growth_rate = np.mean(growth_rates)
                    # Cap growth rate at reasonable levels
                    growth_rate = max(-0.2, min(0.3, growth_rate))
                else:
                    growth_rate = 0.05
            
            # Project future cash flows with declining growth
            projections = []
            terminal_growth = 0.03  # 3% terminal growth
            
            for year in range(1, years + 1):
                # Apply declining growth rate
                year_growth = growth_rate * (1 - (year - 1) / years) + terminal_growth * ((year - 1) / years)
                projected_fcf = latest_fcf * ((1 + year_growth) ** year)
                
                projections.append({
                    'Year': year,
                    'Growth_Rate': year_growth,
                    'Projected_FCF': projected_fcf
                })
            
            projection_df = pd.DataFrame(projections)
            print(f"Projected {years} years of future cash flows")
            return projection_df
            
        except Exception as e:
            print(f"Error projecting future cash flows: {e}")
            return pd.DataFrame()
    
    def calculate_terminal_value(self, final_fcf, wacc, terminal_growth=0.03):
        """
        Calculate terminal value using Gordon Growth Model.
        
        Args:
            final_fcf: Final year projected FCF
            wacc: Weighted Average Cost of Capital
            terminal_growth: Terminal growth rate
            
        Returns:
            float: Terminal value
        """
        try:
            terminal_value = (final_fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
            print(f"Terminal value calculated: ${terminal_value:,.0f}")
            return terminal_value
            
        except Exception as e:
            print(f"Error calculating terminal value: {e}")
            return 0
    
    def calculate_dcf_valuation(self, years=5):
        """
        Calculate DCF intrinsic value with fallback mechanisms.
        
        Args:
            years: Number of years to project
            
        Returns:
            dict: DCF analysis results
        """
        try:
            print(f"\n{'='*60}")
            print(f"DCF ANALYSIS FOR {self.ticker}")
            print(f"{'='*60}")
            
            # Get stock data
            stock_data = self.get_stock_data_with_retry()
            if not stock_data:
                print(" Failed to get stock data, trying fallback method...")
                stock_data = self._get_minimal_stock_data()
                if not stock_data:
                    print("All data fetching methods failed")
                    return None
            
            # Calculate WACC
            wacc = self.calculate_wacc(stock_data)
            
            # Calculate free cash flow
            fcf_data = self.calculate_free_cash_flow(stock_data)
            if fcf_data.empty:
                print(" No cash flow data available, using estimated FCF...")
                fcf_data = self._estimate_free_cash_flow(stock_data)
                if fcf_data.empty:
                    print(" Cannot perform DCF without cash flow data")
                    return None
            
            # Project future cash flows
            projections = self.project_future_cash_flows(fcf_data, years)
            if projections.empty:
                print(" Cannot perform DCF without projections")
                return None
            
            # Calculate present value of projected cash flows
            pv_cash_flows = []
            for _, row in projections.iterrows():
                year = row['Year']
                fcf = row['Projected_FCF']
                pv = fcf / ((1 + wacc) ** year)
                pv_cash_flows.append(pv)
            
            total_pv_cash_flows = sum(pv_cash_flows)
            
            # Calculate terminal value
            final_fcf = projections.iloc[-1]['Projected_FCF']
            terminal_value = self.calculate_terminal_value(final_fcf, wacc)
            pv_terminal_value = terminal_value / ((1 + wacc) ** years)
            
            # Calculate enterprise value
            enterprise_value = total_pv_cash_flows + pv_terminal_value
            
            # Get market data
            info = stock_data['info']
            shares_outstanding = info.get('sharesOutstanding', 1)
            current_price = stock_data['current_price']
            total_debt = info.get('totalDebt', 0)
            total_cash = info.get('totalCash', 0)
            net_debt = total_debt - total_cash
            
            # Calculate equity value
            equity_value = enterprise_value - net_debt
            
            # Calculate per-share value
            dcf_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0
            
            # Calculate upside/downside
            upside_downside = ((dcf_per_share - current_price) / current_price * 100) if current_price > 0 else 0
            
            results = {
                'ticker': self.ticker,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'current_price': current_price,
                'dcf_value_per_share': dcf_per_share,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'terminal_value': terminal_value,
                'wacc': wacc,
                'risk_free_rate': self.risk_free_rate,
                'beta': stock_data['beta'],
                'upside_downside_pct': upside_downside,
                'projections': projections,
                'present_value_cash_flows': total_pv_cash_flows,
                'present_value_terminal': pv_terminal_value,
                'shares_outstanding': shares_outstanding,
                'net_debt': net_debt,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return results
            
        except Exception as e:
            print(f"Error calculating DCF value: {e}")
            return None
    
    def generate_investment_recommendation(self, dcf_results):
        """
        Generate investment recommendation based on DCF analysis.
        
        Args:
            dcf_results: DCF analysis results
            
        Returns:
            dict: Investment recommendation
        """
        if not dcf_results:
            return {'recommendation': 'HOLD', 'rationale': 'Insufficient data for analysis'}
        
        upside = dcf_results['upside_downside_pct']
        
        # Recommendation logic
        if upside > 20:
            recommendation = 'STRONG BUY'
            rationale = f"Significant upside potential of {upside:.1f}%. DCF value significantly exceeds current price."
        elif upside > 10:
            recommendation = 'BUY'
            rationale = f"Attractive upside potential of {upside:.1f}%. Stock appears undervalued."
        elif upside > -5:
            recommendation = 'HOLD'
            rationale = f"Fair value range. Upside of {upside:.1f}% is within normal market fluctuations."
        elif upside > -15:
            recommendation = 'SELL'
            rationale = f"Stock appears overvalued with {upside:.1f}% downside risk."
        else:
            recommendation = 'STRONG SELL'
            rationale = f"Significant overvaluation with {upside:.1f}% downside risk."
        
        # Additional factors
        pe_ratio = dcf_results.get('pe_ratio', 0)
        beta = dcf_results.get('beta', 1.0)
        
        # Adjust recommendation based on additional factors
        if pe_ratio > 30 and upside < 10:
            rationale += " High P/E ratio suggests premium valuation."
        elif pe_ratio < 15 and upside > 5:
            rationale += " Low P/E ratio supports attractive valuation."
        
        if beta > 1.5:
            rationale += " High beta indicates higher volatility and risk."
        elif beta < 0.8:
            rationale += " Low beta suggests defensive characteristics."
        
        return {
            'recommendation': recommendation,
            'rationale': rationale,
            'upside_downside': upside
        }
    
    def display_comprehensive_analysis(self, dcf_results, recommendation):
        """
        Display comprehensive DCF analysis results.
        
        Args:
            dcf_results: DCF analysis results
            recommendation: Investment recommendation
        """
        if not dcf_results:
            print("No DCF analysis results available.")
            return
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE DCF ANALYSIS FOR {self.ticker}")
        print(f"{'='*80}")
        
        # Company Overview
        print(f"\n📊 COMPANY OVERVIEW")
        print(f"{'─'*50}")
        print(f"Company Name: {dcf_results['company_name']}")
        print(f"Sector: {dcf_results['sector']}")
        print(f"Current Price: ${dcf_results['current_price']:.2f}")
        print(f"Market Cap: ${dcf_results['market_cap']:,.0f}")
        print(f"Shares Outstanding: {dcf_results['shares_outstanding']:,.0f}")
        
        # Key Ratios
        print(f"\n📈 KEY FINANCIAL RATIOS")
        print(f"{'─'*50}")
        print(f"P/E Ratio: {dcf_results['pe_ratio']:.2f}")
        print(f"P/B Ratio: {dcf_results['pb_ratio']:.2f}")
        print(f"Beta: {dcf_results['beta']:.2f}")
        
        # DCF Assumptions
        print(f"\n🔧 DCF ASSUMPTIONS")
        print(f"{'─'*50}")
        print(f"Risk-Free Rate: {dcf_results['risk_free_rate']:.2%}")
        print(f"Market Risk Premium: {self.market_risk_premium:.2%}")
        print(f"WACC: {dcf_results['wacc']:.2%}")
        print(f"Beta: {dcf_results['beta']:.2f}")
        
        # DCF Results
        print(f"\n💰 DCF VALUATION RESULTS")
        print(f"{'─'*50}")
        print(f"Current Stock Price: ${dcf_results['current_price']:.2f}")
        print(f"DCF Intrinsic Value: ${dcf_results['dcf_value_per_share']:.2f}")
        print(f"Upside/Downside: {dcf_results['upside_downside_pct']:+.1f}%")
        print(f"Enterprise Value: ${dcf_results['enterprise_value']:,.0f}")
        print(f"Equity Value: ${dcf_results['equity_value']:,.0f}")
        print(f"Terminal Value: ${dcf_results['terminal_value']:,.0f}")
        print(f"PV of Cash Flows: ${dcf_results['present_value_cash_flows']:,.0f}")
        print(f"PV of Terminal Value: ${dcf_results['present_value_terminal']:,.0f}")
        
        # Investment Recommendation
        print(f"\n🎯 INVESTMENT RECOMMENDATION")
        print(f"{'─'*50}")
        print(f"Recommendation: {recommendation['recommendation']}")
        print(f"Rationale: {recommendation['rationale']}")
        
        # Cash Flow Projections
        if not dcf_results['projections'].empty:
            print(f"\n📊 PROJECTED CASH FLOWS (Next {len(dcf_results['projections'])} Years)")
            print(f"{'─'*50}")
            projections_df = dcf_results['projections'].copy()
            projections_df['Present_Value'] = projections_df.apply(
                lambda row: row['Projected_FCF'] / ((1 + dcf_results['wacc']) ** row['Year']), 
                axis=1
            )
            projections_df['Growth_Rate'] = projections_df['Growth_Rate'].apply(lambda x: f"{x:.1%}")
            projections_df['Projected_FCF'] = projections_df['Projected_FCF'].apply(lambda x: f"${x:,.0f}")
            projections_df['Present_Value'] = projections_df['Present_Value'].apply(lambda x: f"${x:,.0f}")
            print(projections_df.to_string(index=False))
        
        print(f"\n{'='*80}")
        print(f"Analysis completed on: {dcf_results['analysis_date']}")
        print(f"{'='*80}")


def main():
    """
    Main function to run standalone DCF analysis.
    """
    print("🏦 STANDALONE DCF VALUATION ANALYZER")
    print("=" * 80)
    print("Complete Discounted Cash Flow Analysis with Investment Recommendations")
    print("=" * 80)
    print("Features:")
    print("• Scrapes real-time financial data")
    print("• Calculates DCF intrinsic value")
    print("• Provides buy/sell/hold recommendations")
    print("• Handles rate limiting and API errors")
    print("• Uses robust financial modeling")
    print("=" * 80)
    
    while True:
        # Get user input
        ticker = input("\nEnter stock ticker symbol (e.g., AAPL, MSFT, GOOGL) or 'quit' to exit: ").upper().strip()
        
        if ticker.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thank you for using the DCF Analyzer!")
            break
        
        if not ticker:
            print("❌ Please enter a valid ticker symbol.")
            continue
        
        # Validate ticker format
        if len(ticker) < 1 or len(ticker) > 5:
            print("❌ Invalid ticker format. Please enter a valid ticker symbol (1-5 characters).")
            continue
        
        # Initialize analyzer
        analyzer = StandaloneDCFAnalyzer(ticker)
        
        # Run analysis
        print(f"\n🔄 Analyzing {ticker}...")
        dcf_results = analyzer.calculate_dcf_valuation(years=5)
        
        if dcf_results:
            # Generate recommendation
            recommendation = analyzer.generate_investment_recommendation(dcf_results)
            
            # Display results
            analyzer.display_comprehensive_analysis(dcf_results, recommendation)
            
            print(f"\n🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"📈 FINAL RECOMMENDATION: {recommendation['recommendation']}")
            print(f"💰 DCF Intrinsic Value: ${dcf_results['dcf_value_per_share']:.2f}")
            print(f"📊 Current Market Price: ${dcf_results['current_price']:.2f}")
            print(f"📈 Upside/Downside: {dcf_results['upside_downside_pct']:+.1f}%")
            print(f"🏢 Company: {dcf_results['company_name']}")
            print(f"🏭 Sector: {dcf_results['sector']}")
            print(f"📅 Analysis Date: {dcf_results['analysis_date']}")
            print("=" * 80)
            
            # Ask if user wants to analyze another stock
            while True:
                another = input(f"\nWould you like to analyze another stock? (y/n): ").lower().strip()
                if another in ['y', 'yes']:
                    # Add delay before analyzing next stock to prevent rate limiting
                    print("\n⏳ Waiting 10 seconds before next analysis to prevent rate limiting...")
                    time.sleep(10)
                    RateLimiter.wait_if_needed()
                    break
                elif another in ['n', 'no']:
                    print("\n👋 Thank you for using the DCF Analyzer!")
                    return
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        else:
            print(f"\n❌ Analysis failed for {ticker}. Please try again with a different ticker.")
            # Reset rate limiter on failure to allow retry
            RateLimiter.reset()


def demo_mode():
    """
    Run demo mode with Apple (AAPL).
    """
    print("🏦 STANDALONE DCF VALUATION ANALYZER - DEMO MODE")
    print("=" * 80)
    print("Running demo analysis for Apple (AAPL)...")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = StandaloneDCFAnalyzer("AAPL")
    
    # Run analysis
    dcf_results = analyzer.calculate_dcf_valuation(years=5)
    
    if dcf_results:
        # Generate recommendation
        recommendation = analyzer.generate_investment_recommendation(dcf_results)
        
        # Display results
        analyzer.display_comprehensive_analysis(dcf_results, recommendation)
        
        print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"📈 Recommendation: {recommendation['recommendation']}")
        print(f"💰 DCF Value: ${dcf_results['dcf_value_per_share']:.2f}")
        print(f"📊 Current Price: ${dcf_results['current_price']:.2f}")
        print(f"📈 Upside/Downside: {dcf_results['upside_downside_pct']:+.1f}%")
        print("=" * 80)
        print("\n💡 To analyze other stocks, run: python standalone_dcf_analyzer.py")
    else:
        print("\n❌ Demo failed. Please check your internet connection.")


if __name__ == "__main__":
    import sys
    
    # Check if demo mode is requested
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'demo':
        demo_mode()
    else:
        main()
