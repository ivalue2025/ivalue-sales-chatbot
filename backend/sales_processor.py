import pandas as pd
import google.generativeai as genai  # type: ignore
from google.generativeai import configure, GenerativeModel  # type: ignore
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import warnings
import re
import numpy as np
from typing import Union, List, Dict, Any
warnings.filterwarnings('ignore')

# Configure the API key
# Option 1: Using environment variable
configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Option 2: Direct configuration (less secure)
# configure(api_key="your_api_key_here")

# Initialize the model
model = GenerativeModel('gemini-1.5-flash')

# Test the model
try:
    response = model.generate_content("Hello, how are you?")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
    print("Make sure your API key is set correctly!")

def format_in_crores(value):
    """Format value in Indian Crores (1 Crore = 10,000,000)"""
    if pd.isna(value):
        return "₹0"
    crore_value = value / 10000000
    return f"₹{crore_value:,.2f} Cr"

class SalesDataProcessor:
    def __init__(self, df):
        self.df = df
        self.summary_stats = {}
        self.yearly_stats = {}
        self.dimension_combinations = {}
        self.partner_stats = {}
        self.oem_stats = {}
        self.partner_customer_stats = {}  # New: Store partner-end customer relationships
        self.vertical_stats = {}  # New: Store vertical performance stats
        self.customer_stats = {}  # NEW: Store end customer performance stats
        self.prepare_data()


    def get_unique_values(self, column):
        """Get unique values for a column (optimized)"""
        if column in self.df.columns:
            return self.df[column].unique().tolist()
        return []
    

    def get_vertical_performance(self, vertical_name, year=None):
        """Get comprehensive vertical performance metrics"""
        vertical_data = self.df[self.df['Vertical'].str.lower() == vertical_name.lower()]
        
        if year:
            vertical_data = vertical_data[vertical_data['Year_Start'] == year]
            if vertical_data.empty:
                return None
        
        return {
            'total_revenue': vertical_data['TL Base Value'].sum(),
            'total_margin': vertical_data['Gross Margin Value'].sum(),
            'transaction_count': len(vertical_data),
            'gm_percent': (vertical_data['Gross Margin Value'].sum() / 
                        vertical_data['TL Base Value'].sum() * 100) if vertical_data['TL Base Value'].sum() > 0 else 0,
            'top_partner': vertical_data.groupby('Partner')['TL Base Value'].sum().idxmax() if not vertical_data.empty else None,
            'top_customer': vertical_data.groupby('End Customer')['TL Base Value'].sum().idxmax() if not vertical_data.empty else None,
            'top_oem': vertical_data.groupby('OEM')['TL Base Value'].sum().idxmax() if not vertical_data.empty else None
        }

    def get_channel_performance(self, channel_name, year=None):
        """Get comprehensive channel performance metrics"""
        channel_data = self.df[self.df['Channel'].str.lower() == channel_name.lower()]
        
        if year:
            channel_data = channel_data[channel_data['Year_Start'] == year]
            if channel_data.empty:
                return None
        
        return {
            'total_revenue': channel_data['TL Base Value'].sum(),
            'total_margin': channel_data['Gross Margin Value'].sum(),
            'transaction_count': len(channel_data),
            'gm_percent': (channel_data['Gross Margin Value'].sum() / 
                        channel_data['TL Base Value'].sum() * 100) if channel_data['TL Base Value'].sum() > 0 else 0,
            'top_partner': channel_data.groupby('Partner')['TL Base Value'].sum().idxmax() if not channel_data.empty else None,
            'top_oem': channel_data.groupby('OEM')['TL Base Value'].sum().idxmax() if not channel_data.empty else None
        }
    
    def get_customer_performance(self, customer_name, year=None):
        """Get comprehensive customer performance metrics"""
        customer_data = self.df[self.df['End Customer'].str.lower() == customer_name.lower()]
        
        if year:
            customer_data = customer_data[customer_data['Year_Start'] == year]
            if customer_data.empty:
                return None
        
        return {
            'total_revenue': customer_data['TL Base Value'].sum(),
            'total_margin': customer_data['Gross Margin Value'].sum(),
            'transaction_count': len(customer_data),
            'gm_percent': (customer_data['Gross Margin Value'].sum() / 
                        customer_data['TL Base Value'].sum() * 100) if customer_data['TL Base Value'].sum() > 0 else 0,
            'first_transaction': customer_data['A/R Posting Date'].min(),
            'last_transaction': customer_data['A/R Posting Date'].max()
        }
    
    def get_partner_performance(self, partner_name, year=None):
        """Get comprehensive partner performance for a specific year"""
        partner_data = self.df[self.df['Partner'].str.lower() == partner_name.lower()]
        
        if year:
            partner_data = partner_data[partner_data['Year_Start'] == year]
            if partner_data.empty:
                return None
        
        return {
            'total_revenue': partner_data['TL Base Value'].sum(),
            'total_margin': partner_data['Gross Margin Value'].sum(),
            'transaction_count': len(partner_data),
            'gm_percent': (partner_data['Gross Margin Value'].sum() / 
                        partner_data['TL Base Value'].sum() * 100) if partner_data['TL Base Value'].sum() > 0 else 0
        }

    def filter_data(self, filters):
        """
        Filter data based on multiple criteria
        filters: dict of {column: [values]}
        """
        filtered_df = self.df.copy()
        for column, values in filters.items():
            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].isin(values)]
        return filtered_df

    def prepare_data(self):
        """Optimize data for large files and handle fiscal year ranges"""
        print("🔄 Processing data for optimal performance...")
        print("Columns in DataFrame:", self.df.columns.tolist())
        
        # Convert column names to match expected format
        column_mappings = {
            'Vertical Account': 'Vertical',
            'End Customer Name': 'End Customer',
            'A/R Posting Date': 'A/R Posting Date',
            'Business Head Name': 'Business Head Name',
            'Group Business Manager Name': 'Group Business Manager Name',
            'Business Manager Name': 'Business Manager Name',
            'Group Channel Champ': 'Group Channel Champ',
            'Channel Champ': 'Channel Champ',
            'Vertical Champ': 'Vertical Champ'
        }
        
        for old_name, new_name in column_mappings.items():
            if old_name in self.df.columns:
                self.df.rename(columns={old_name: new_name}, inplace=True)
        
        # Convert fiscal years like "FY23" or "2022-23" into start and end years
        if 'Year' in self.df.columns and self.df['Year'].dtype == object:
            print("🔧 Parsing fiscal year ranges...")
            try:
                # Initialize Year_Start and Year_End columns
                self.df['Year_Start'] = None
                self.df['Year_End'] = None
                
                # Handle formats like FY23, FY24, etc.
                fy_mask = self.df['Year'].str.startswith('FY', na=False)
                if fy_mask.any():
                    self.df.loc[fy_mask, 'Year_Start'] = (
                        self.df.loc[fy_mask, 'Year']
                        .str.replace('FY', '')
                        .astype(int) + 2000
                    )
                    self.df.loc[fy_mask, 'Year_End'] = self.df.loc[fy_mask, 'Year_Start'] + 1
                
                # Handle formats like 2022-23, 2023-24, etc.
                dash_mask = self.df['Year'].str.contains('-', na=False) & ~fy_mask
                if dash_mask.any():
                    year_split = self.df.loc[dash_mask, 'Year'].str.split('-')
                    self.df.loc[dash_mask, 'Year_Start'] = year_split.str[0].astype(int)
                    
                    # Handle 2-digit and 4-digit end years
                    end_years = year_split.str[1].astype(int)
                    # If end year is 2-digit, add 2000
                    end_years = end_years.apply(lambda x: x + 2000 if x < 100 else x)
                    self.df.loc[dash_mask, 'Year_End'] = end_years
                
                # Handle 4-digit years (like 2023)
                numeric_mask = self.df['Year'].str.isdigit()
                if numeric_mask.any():
                    self.df.loc[numeric_mask, 'Year_Start'] = self.df.loc[numeric_mask, 'Year'].astype(int)
                    self.df.loc[numeric_mask, 'Year_End'] = self.df.loc[numeric_mask, 'Year_Start'] + 1
                
                # Convert to int
                self.df['Year_Start'] = self.df['Year_Start'].astype(int)
                self.df['Year_End'] = self.df['Year_End'].astype(int)
                
                print(f"✅ Years parsed: {sorted(self.df['Year_Start'].unique())}")
            except Exception as e:
                print(f"❌ Failed to parse Year column: {e}")
        
        # Convert date columns
        date_columns = ['A/R Posting Date']
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        # Create summary statistics for faster queries
        self.create_summary_stats()
        
        # Create yearly statistics for comparisons
        self.create_yearly_stats()
        
        # Create dimension combinations
        self.create_dimension_combinations()
        
        # Create partner/OEM performance stats
        self.create_partner_stats()
        self.create_oem_stats()
        
        # Create partner-customer relationships
        self.create_partner_customer_stats()
        
        # Create vertical performance stats
        self.create_vertical_stats()
        
        # Create end customer performance stats
        self.create_customer_stats()
        
        # Add Business Manager statistics if column exists
        if 'Business Manager' in self.df.columns:
            self.create_business_manager_stats()
        
        # Add Group Business Manager to dimensions if column exists
        if 'Group Business Manager Name' in self.df.columns:
            self.create_group_business_manager_stats()
        
        # Create indexes for faster searching
        self.create_indexes()
        
        print("✅ Data processing complete!")

    def create_group_business_manager_stats(self):
        """Create Group Business Manager performance statistics"""
        try:
            print("🔄 Creating Group Business Manager performance statistics...")
            
            # Initialize group_business_manager_stats if it doesn't exist
            if not hasattr(self, 'group_business_manager_stats'):
                self.group_business_manager_stats = {}
            
            managers = self.df['Group Business Manager Name'].unique().tolist()

            for manager in managers:
                manager_data = self.df[self.df['Group Business Manager Name'] == manager]
                
                self.group_business_manager_stats[manager] = {
                    'total_revenue': manager_data['TL Base Value'].sum(),
                    'total_margin': manager_data['Gross Margin Value'].sum(),
                    'transaction_count': len(manager_data),
                    'first_transaction': manager_data['A/R Posting Date'].min(),
                    'last_transaction': manager_data['A/R Posting Date'].max()
                }
                
                # Add yearly breakdown if available
                if 'Year_Start' in self.df.columns:
                    yearly_data = manager_data.groupby('Year_Start').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum',
                        'A/R Posting Date': 'count'
                    })
                    self.group_business_manager_stats[manager]['yearly_data'] = yearly_data.to_dict('index')

            print(f"✅ Created performance stats for {len(managers)} Group Business Managers")

        except Exception as e:
            print(f"⚠️ Warning: Could not create Group Business Manager stats: {e}")

    def create_business_manager_stats(self):
        """Create Business Manager performance statistics"""
        try:
            print("🔄 Creating Business Manager performance statistics...")
            managers = self.df['Business Manager'].unique().tolist()
            
            # Initialize business_manager_stats if it doesn't exist
            if not hasattr(self, 'business_manager_stats'):
                self.business_manager_stats = {}
            
            for manager in managers:
                manager_data = self.df[self.df['Business Manager'] == manager]
                
                self.business_manager_stats[manager] = {
                    'total_revenue': manager_data['TL Base Value'].sum(),
                    'total_margin': manager_data['Gross Margin Value'].sum(),
                    'transaction_count': len(manager_data),
                    'first_transaction': manager_data['A/R Posting Date'].min(),
                    'last_transaction': manager_data['A/R Posting Date'].max()
                }
                
                # Add yearly breakdown if available
                if 'Year_Start' in self.df.columns:
                    yearly_data = manager_data.groupby('Year_Start').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum',
                        'A/R Posting Date': 'count'
                    })
                    self.business_manager_stats[manager]['yearly_data'] = yearly_data.to_dict('index')
            
            print(f"✅ Created performance stats for {len(managers)} Business Managers")
        except Exception as e:
            print(f"⚠️ Warning: Could not create Business Manager stats: {e}")

    def create_summary_stats(self):
        """Create summary statistics for common queries"""
        try:
            # Numerical summaries
            if 'Gross Margin Value' in self.df.columns:
                self.summary_stats['total_gross_margin'] = self.df['Gross Margin Value'].sum()
                self.summary_stats['avg_gross_margin'] = self.df['Gross Margin Value'].mean()

            if 'TL Base Value' in self.df.columns:
                self.summary_stats['total_revenue'] = self.df['TL Base Value'].sum()
                self.summary_stats['avg_revenue'] = self.df['TL Base Value'].mean()

            # Categorical summaries
            categorical_columns = ['Region', 'Partner', 'OEM', 'Channel', 'Vertical', 'End Customer']
            for col in categorical_columns:
                if col in self.df.columns:
                    self.summary_stats[f'{col.lower()}_counts'] = self.df[col].value_counts().to_dict()
                    self.summary_stats[f'{col.lower()}_values'] = self.df[col].unique().tolist()

            # Channel-specific summaries
            if 'Channel' in self.df.columns:
                self.summary_stats['channel_performance'] = self.df.groupby('Channel')['TL Base Value'].sum().to_dict()
                self.summary_stats['channel_margin'] = self.df.groupby('Channel')['Gross Margin Value'].sum().to_dict()

            # Time-based summaries
            if 'Year_Start' in self.df.columns:
                self.summary_stats['yearly_sales'] = self.df.groupby('Year_Start')['TL Base Value'].sum().to_dict() if 'TL Base Value' in self.df.columns else {}

        except Exception as e:
            print(f"⚠️ Warning: Could not create all summary stats: {e}")

    def create_yearly_stats(self):
        """Create comprehensive yearly statistics for comparisons"""
        try:
            if 'Year_Start' not in self.df.columns:
                print("⚠️ Warning: No 'Year' column found for yearly comparisons")
                return

            # Get all available years
            years = sorted(self.df['Year_Start'].unique())
            print(f"📅 Available years: {years}")

            # Create yearly breakdown for each metric
            for year in years:
                year_data = self.df[self.df['Year_Start'] == year]

                self.yearly_stats[year] = {
                    'total_transactions': len(year_data),
                    'total_revenue': year_data['TL Base Value'].sum() if 'TL Base Value' in self.df.columns else 0,
                    'avg_revenue': year_data['TL Base Value'].mean() if 'TL Base Value' in self.df.columns else 0,
                    'total_gross_margin': year_data['Gross Margin Value'].sum() if 'Gross Margin Value' in self.df.columns else 0,
                    'avg_gross_margin': year_data['Gross Margin Value'].mean() if 'Gross Margin Value' in self.df.columns else 0,
                }

                # Add channel breakdown by year
                if 'Channel' in self.df.columns:
                    self.yearly_stats[year]['channel_revenue'] = year_data.groupby('Channel')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['channel_margin'] = year_data.groupby('Channel')['Gross Margin Value'].sum().to_dict()

                # Add regional breakdown by year
                if 'Region' in self.df.columns:
                    self.yearly_stats[year]['region_revenue'] = year_data.groupby('Region')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['region_margin'] = year_data.groupby('Region')['Gross Margin Value'].sum().to_dict()

                # Add vertical breakdown by year
                if 'Vertical' in self.df.columns:
                    self.yearly_stats[year]['vertical_revenue'] = year_data.groupby('Vertical')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['vertical_margin'] = year_data.groupby('Vertical')['Gross Margin Value'].sum().to_dict()

                # Add partner breakdown by year
                if 'Partner' in self.df.columns:
                    self.yearly_stats[year]['partner_revenue'] = year_data.groupby('Partner')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['partner_margin'] = year_data.groupby('Partner')['Gross Margin Value'].sum().to_dict()

                # Add OEM breakdown by year
                if 'OEM' in self.df.columns:
                    self.yearly_stats[year]['oem_revenue'] = year_data.groupby('OEM')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['oem_margin'] = year_data.groupby('OEM')['Gross Margin Value'].sum().to_dict()

                # Add End Customer breakdown by year
                if 'End Customer' in self.df.columns:
                    self.yearly_stats[year]['customer_revenue'] = year_data.groupby('End Customer')['TL Base Value'].sum().to_dict()
                    self.yearly_stats[year]['customer_margin'] = year_data.groupby('End Customer')['Gross Margin Value'].sum().to_dict()

            # Create comparison metrics
            self.create_comparison_metrics()

        except Exception as e:
            print(f"⚠️ Warning: Could not create yearly stats: {e}")

    def create_partner_stats(self):
        """Create comprehensive partner performance statistics"""
        try:
            if 'Partner' not in self.df.columns:
                print("⚠️ Warning: No 'Partner' column found")
                return

            print("🔄 Creating partner performance statistics...")

            # Get all unique partners
            partners = self.df['Partner'].unique().tolist()

            for partner in partners:
                partner_data = self.df[self.df['Partner'] == partner]

                # Basic stats
                self.partner_stats[partner] = {
                    'total_revenue': partner_data['TL Base Value'].sum() if 'TL Base Value' in self.df.columns else 0,
                    'total_margin': partner_data['Gross Margin Value'].sum() if 'Gross Margin Value' in self.df.columns else 0,
                    'transaction_count': len(partner_data),
                    'first_transaction': partner_data['A/R Posting Date'].min() if 'A/R Posting Date' in self.df.columns else None,
                    'last_transaction': partner_data['A/R Posting Date'].max() if 'A/R Posting Date' in self.df.columns else None
                }

                # Regional performance
                if 'Region' in self.df.columns:
                    regional_revenue = partner_data.groupby('Region')['TL Base Value'].sum().to_dict()
                    regional_margin = partner_data.groupby('Region')['Gross Margin Value'].sum().to_dict()
                    self.partner_stats[partner]['regional_revenue'] = regional_revenue
                    self.partner_stats[partner]['regional_margin'] = regional_margin
                    self.partner_stats[partner]['top_region'] = max(regional_revenue.items(), key=lambda x: x[1])[0] if regional_revenue else None

                # Yearly performance
                if 'Year_Start' in self.df.columns:
                    yearly_revenue = partner_data.groupby('Year_Start')['TL Base Value'].sum().to_dict()
                    yearly_margin = partner_data.groupby('Year_Start')['Gross Margin Value'].sum().to_dict()
                    self.partner_stats[partner]['yearly_revenue'] = yearly_revenue
                    self.partner_stats[partner]['yearly_margin'] = yearly_margin
                    self.partner_stats[partner]['best_year'] = max(yearly_revenue.items(), key=lambda x: x[1])[0] if yearly_revenue else None

                # Yearly-Regional performance
                if 'Year_Start' in self.df.columns and 'Region' in self.df.columns:
                    yearly_regional = partner_data.groupby(['Year_Start', 'Region']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.partner_stats[partner]['yearly_regional_data'] = yearly_regional.to_dict('records')

                # Vertical performance
                if 'Vertical' in self.df.columns:
                    vertical_revenue = partner_data.groupby('Vertical')['TL Base Value'].sum().to_dict()
                    vertical_margin = partner_data.groupby('Vertical')['Gross Margin Value'].sum().to_dict()
                    self.partner_stats[partner]['vertical_revenue'] = vertical_revenue
                    self.partner_stats[partner]['vertical_margin'] = vertical_margin
                    self.partner_stats[partner]['top_vertical'] = max(vertical_revenue.items(), key=lambda x: x[1])[0] if vertical_revenue else None

            print(f"✅ Created performance stats for {len(partners)} partners")

        except Exception as e:
            print(f"⚠️ Warning: Could not create partner stats: {e}")

    def create_oem_stats(self):
        """Create comprehensive OEM performance statistics"""
        try:
            if 'OEM' not in self.df.columns:
                print("⚠️ Warning: No 'OEM' column found")
                return

            print("🔄 Creating OEM performance statistics...")

            # Get all unique OEMs
            oems = self.df['OEM'].unique().tolist()

            for oem in oems:
                oem_data = self.df[self.df['OEM'] == oem]

                # Basic stats
                self.oem_stats[oem] = {
                    'total_revenue': oem_data['TL Base Value'].sum() if 'TL Base Value' in self.df.columns else 0,
                    'total_margin': oem_data['Gross Margin Value'].sum() if 'Gross Margin Value' in self.df.columns else 0,
                    'transaction_count': len(oem_data),
                    'first_transaction': oem_data['A/R Posting Date'].min() if 'A/R Posting Date' in self.df.columns else None,
                    'last_transaction': oem_data['A/R Posting Date'].max() if 'A/R Posting Date' in self.df.columns else None
                }

                # Regional performance
                if 'Region' in self.df.columns:
                    regional_revenue = oem_data.groupby('Region')['TL Base Value'].sum().to_dict()
                    regional_margin = oem_data.groupby('Region')['Gross Margin Value'].sum().to_dict()
                    self.oem_stats[oem]['regional_revenue'] = regional_revenue
                    self.oem_stats[oem]['regional_margin'] = regional_margin
                    self.oem_stats[oem]['top_region'] = max(regional_revenue.items(), key=lambda x: x[1])[0] if regional_revenue else None

                # Yearly performance
                if 'Year_Start' in self.df.columns:
                    yearly_revenue = oem_data.groupby('Year_Start')['TL Base Value'].sum().to_dict()
                    yearly_margin = oem_data.groupby('Year_Start')['Gross Margin Value'].sum().to_dict()
                    self.oem_stats[oem]['yearly_revenue'] = yearly_revenue
                    self.oem_stats[oem]['yearly_margin'] = yearly_margin
                    self.oem_stats[oem]['best_year'] = max(yearly_revenue.items(), key=lambda x: x[1])[0] if yearly_revenue else None

                # Yearly-Regional performance
                if 'Year_Start' in self.df.columns and 'Region' in self.df.columns:
                    yearly_regional = oem_data.groupby(['Year_Start', 'Region']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.oem_stats[oem]['yearly_regional_data'] = yearly_regional.to_dict('records')

                # Vertical performance
                if 'Vertical' in self.df.columns:
                    vertical_revenue = oem_data.groupby('Vertical')['TL Base Value'].sum().to_dict()
                    vertical_margin = oem_data.groupby('Vertical')['Gross Margin Value'].sum().to_dict()
                    self.oem_stats[oem]['vertical_revenue'] = vertical_revenue
                    self.oem_stats[oem]['vertical_margin'] = vertical_margin
                    self.oem_stats[oem]['top_vertical'] = max(vertical_revenue.items(), key=lambda x: x[1])[0] if vertical_revenue else None

            print(f"✅ Created performance stats for {len(oems)} OEMs")

        except Exception as e:
            print(f"⚠️ Warning: Could not create OEM stats: {e}")

    def create_partner_customer_stats(self):
        """Create partner-end customer relationship statistics"""
        try:
            if 'Partner' not in self.df.columns or 'End Customer' not in self.df.columns:
                print("⚠️ Warning: No 'Partner' or 'End Customer' column found")
                return

            print("🔄 Creating partner-customer relationship statistics...")

            # Group by Partner and End Customer
            partner_customer_data = self.df.groupby(['Partner', 'End Customer']).agg({
                'TL Base Value': 'sum',
                'Gross Margin Value': 'sum',
                'A/R Posting Date': ['min', 'max', 'count']
            }).reset_index()

            # Flatten multi-index columns
            partner_customer_data.columns = ['Partner', 'End Customer', 'Total Revenue',
                                          'Total Margin', 'First Transaction',
                                          'Last Transaction', 'Transaction Count']

            # Group by Partner to create summary
            for partner, group in partner_customer_data.groupby('Partner'):
                self.partner_customer_stats[partner] = {
                    'total_customers': len(group),
                    'top_customers': group.nlargest(5, 'Total Revenue')[['End Customer', 'Total Revenue']].to_dict('records'),
                    'total_revenue': group['Total Revenue'].sum(),
                    'total_margin': group['Total Margin'].sum(),
                    'customer_details': group.to_dict('records')
                }

            print(f"✅ Created customer stats for {len(self.partner_customer_stats)} partners")

        except Exception as e:
            print(f"⚠️ Warning: Could not create partner-customer stats: {e}")

    def create_vertical_stats(self):
        """Create vertical performance statistics"""
        try:
            if 'Vertical' not in self.df.columns:
                print("⚠️ Warning: No 'Vertical' column found")
                return

            print("🔄 Creating vertical performance statistics...")

            # Get all unique verticals
            verticals = self.df['Vertical'].unique().tolist()

            for vertical in verticals:
                vertical_data = self.df[self.df['Vertical'] == vertical]

                # Basic stats
                self.vertical_stats[vertical] = {
                    'total_revenue': vertical_data['TL Base Value'].sum() if 'TL Base Value' in self.df.columns else 0,
                    'total_margin': vertical_data['Gross Margin Value'].sum() if 'Gross Margin Value' in self.df.columns else 0,
                    'transaction_count': len(vertical_data),
                    'first_transaction': vertical_data['A/R Posting Date'].min() if 'A/R Posting Date' in self.df.columns else None,
                    'last_transaction': vertical_data['A/R Posting Date'].max() if 'A/R Posting Date' in self.df.columns else None
                }

                # Regional performance
                if 'Region' in self.df.columns:
                    regional_revenue = vertical_data.groupby('Region')['TL Base Value'].sum().to_dict()
                    regional_margin = vertical_data.groupby('Region')['Gross Margin Value'].sum().to_dict()
                    self.vertical_stats[vertical]['regional_revenue'] = regional_revenue
                    self.vertical_stats[vertical]['regional_margin'] = regional_margin
                    self.vertical_stats[vertical]['top_region'] = max(regional_revenue.items(), key=lambda x: x[1])[0] if regional_revenue else None

                # Yearly performance
                if 'Year_Start' in self.df.columns:
                    yearly_revenue = vertical_data.groupby('Year_Start')['TL Base Value'].sum().to_dict()
                    yearly_margin = vertical_data.groupby('Year_Start')['Gross Margin Value'].sum().to_dict()
                    self.vertical_stats[vertical]['yearly_revenue'] = yearly_revenue
                    self.vertical_stats[vertical]['yearly_margin'] = yearly_margin
                    self.vertical_stats[vertical]['best_year'] = max(yearly_revenue.items(), key=lambda x: x[1])[0] if yearly_revenue else None

                # Partner performance
                if 'Partner' in self.df.columns:
                    partner_revenue = vertical_data.groupby('Partner')['TL Base Value'].sum().to_dict()
                    partner_margin = vertical_data.groupby('Partner')['Gross Margin Value'].sum().to_dict()
                    self.vertical_stats[vertical]['partner_revenue'] = partner_revenue
                    self.vertical_stats[vertical]['partner_margin'] = partner_margin
                    self.vertical_stats[vertical]['top_partner'] = max(partner_revenue.items(), key=lambda x: x[1])[0] if partner_revenue else None

                # OEM performance
                if 'OEM' in self.df.columns:
                    oem_revenue = vertical_data.groupby('OEM')['TL Base Value'].sum().to_dict()
                    oem_margin = vertical_data.groupby('OEM')['Gross Margin Value'].sum().to_dict()
                    self.vertical_stats[vertical]['oem_revenue'] = oem_revenue
                    self.vertical_stats[vertical]['oem_margin'] = oem_margin
                    self.vertical_stats[vertical]['top_oem'] = max(oem_revenue.items(), key=lambda x: x[1])[0] if oem_revenue else None

            print(f"✅ Created performance stats for {len(verticals)} verticals")

        except Exception as e:
            print(f"⚠️ Warning: Could not create vertical stats: {e}")

    def create_customer_stats(self):
        """Create end customer performance statistics"""
        try:
            if 'End Customer' not in self.df.columns:
                print("⚠️ Warning: No 'End Customer' column found")
                return

            print("🔄 Creating end customer performance statistics...")

            # Get all unique customers
            customers = self.df['End Customer'].unique().tolist()

            for customer in customers:
                customer_data = self.df[self.df['End Customer'] == customer]

                # Basic stats
                self.customer_stats[customer] = {
                    'total_revenue': customer_data['TL Base Value'].sum() if 'TL Base Value' in self.df.columns else 0,
                    'total_margin': customer_data['Gross Margin Value'].sum() if 'Gross Margin Value' in self.df.columns else 0,
                    'transaction_count': len(customer_data),
                    'first_transaction': customer_data['A/R Posting Date'].min() if 'A/R Posting Date' in self.df.columns else None,
                    'last_transaction': customer_data['A/R Posting Date'].max() if 'A/R Posting Date' in self.df.columns else None
                }

                # Regional performance
                if 'Region' in self.df.columns:
                    regional_revenue = customer_data.groupby('Region')['TL Base Value'].sum().to_dict()
                    regional_margin = customer_data.groupby('Region')['Gross Margin Value'].sum().to_dict()
                    self.customer_stats[customer]['regional_revenue'] = regional_revenue
                    self.customer_stats[customer]['regional_margin'] = regional_margin
                    self.customer_stats[customer]['top_region'] = max(regional_revenue.items(), key=lambda x: x[1])[0] if regional_revenue else None

                # Yearly performance
                if 'Year_Start' in self.df.columns:
                    yearly_revenue = customer_data.groupby('Year_Start')['TL Base Value'].sum().to_dict()
                    yearly_margin = customer_data.groupby('Year_Start')['Gross Margin Value'].sum().to_dict()
                    self.customer_stats[customer]['yearly_revenue'] = yearly_revenue
                    self.customer_stats[customer]['yearly_margin'] = yearly_margin
                    self.customer_stats[customer]['best_year'] = max(yearly_revenue.items(), key=lambda x: x[1])[0] if yearly_revenue else None

                # Partner performance
                if 'Partner' in self.df.columns:
                    partner_revenue = customer_data.groupby('Partner')['TL Base Value'].sum().to_dict()
                    partner_margin = customer_data.groupby('Partner')['Gross Margin Value'].sum().to_dict()
                    self.customer_stats[customer]['partner_revenue'] = partner_revenue
                    self.customer_stats[customer]['partner_margin'] = partner_margin
                    self.customer_stats[customer]['top_partner'] = max(partner_revenue.items(), key=lambda x: x[1])[0] if partner_revenue else None

                # Vertical performance
                if 'Vertical' in self.df.columns:
                    vertical_revenue = customer_data.groupby('Vertical')['TL Base Value'].sum().to_dict()
                    vertical_margin = customer_data.groupby('Vertical')['Gross Margin Value'].sum().to_dict()
                    self.customer_stats[customer]['vertical_revenue'] = vertical_revenue
                    self.customer_stats[customer]['vertical_margin'] = vertical_margin
                    self.customer_stats[customer]['top_vertical'] = max(vertical_revenue.items(), key=lambda x: x[1])[0] if vertical_revenue else None

            print(f"✅ Created performance stats for {len(customers)} end customers")

        except Exception as e:
            print(f"⚠️ Warning: Could not create customer stats: {e}")

    def create_dimension_combinations(self):
        """Create pre-computed combinations of dimensions for faster querying"""
        try:
            # Original dimensions plus new ones
            dimensions = [
                'Year_Start', 'Channel', 'Region', 'Vertical', 'Partner', 'OEM', 'End Customer',
                'Business Head', 'Group Business Manager', 'Business Manager',
                'Group Channel Champ', 'Channel Champ', 'Vertical Champ'
            ]
            
            available_dims = [dim for dim in dimensions if dim in self.df.columns]
            
            # Create all 2-way combinations including the new ones
            for i in range(len(available_dims)):
                for j in range(i+1, len(available_dims)):
                    dim1 = available_dims[i]
                    dim2 = available_dims[j]
                    key = f"{dim1}_{dim2}"
                    
                    # Calculate revenue and margin for each combination
                    grouped = self.df.groupby([dim1, dim2]).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    
                    self.dimension_combinations[key] = grouped

            # Create all 3-way combinations (from original)
            if len(available_dims) >= 3:
                for i in range(len(available_dims)):
                    for j in range(i+1, len(available_dims)):
                        for k in range(j+1, len(available_dims)):
                            dim1 = available_dims[i]
                            dim2 = available_dims[j]
                            dim3 = available_dims[k]
                            key = f"{dim1}_{dim2}_{dim3}"

                            grouped = self.df.groupby([dim1, dim2, dim3]).agg({
                                'TL Base Value': 'sum',
                                'Gross Margin Value': 'sum'
                            }).reset_index()

                            self.dimension_combinations[key] = grouped

            # Create Partner/OEM specific combinations (from original)
            if 'Partner' in available_dims and 'Region' in available_dims:
                key = "Partner_Region_Year"
                grouped = self.df.groupby(['Partner', 'Region', 'Year_Start']).agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).reset_index()
                self.dimension_combinations[key] = grouped

            if 'OEM' in available_dims and 'Region' in available_dims:
                key = "OEM_Region_Year"
                grouped = self.df.groupby(['OEM', 'Region', 'Year_Start']).agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).reset_index()
                self.dimension_combinations[key] = grouped

            # Partner-End Customer combinations (from original)
            if 'Partner' in available_dims and 'End Customer' in available_dims:
                key = "Partner_EndCustomer"
                grouped = self.df.groupby(['Partner', 'End Customer']).agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum',
                    'A/R Posting Date': ['min', 'max', 'count']
                }).reset_index()
                grouped.columns = ['Partner', 'End Customer', 'Total Revenue',
                                'Total Margin', 'First Transaction',
                                'Last Transaction', 'Transaction Count']
                self.dimension_combinations[key] = grouped

            # Vertical combinations (from original)
            if 'Vertical' in available_dims:
                if 'Region' in available_dims:
                    key = "Vertical_Region"
                    grouped = self.df.groupby(['Vertical', 'Region']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

                if 'Partner' in available_dims:
                    key = "Vertical_Partner"
                    grouped = self.df.groupby(['Vertical', 'Partner']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

                if 'OEM' in available_dims:
                    key = "Vertical_OEM"
                    grouped = self.df.groupby(['Vertical', 'OEM']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

                if 'Year_Start' in available_dims:
                    key = "Vertical_Year"
                    grouped = self.df.groupby(['Vertical', 'Year_Start']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

            # End Customer combinations (from original)
            if 'End Customer' in available_dims:
                if 'Region' in available_dims:
                    key = "EndCustomer_Region"
                    grouped = self.df.groupby(['End Customer', 'Region']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

                if 'Vertical' in available_dims:
                    key = "EndCustomer_Vertical"
                    grouped = self.df.groupby(['End Customer', 'Vertical']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

                if 'Year_Start' in available_dims:
                    key = "EndCustomer_Year"
                    grouped = self.df.groupby(['End Customer', 'Year_Start']).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

            # Create specific 3-way combinations (from new requirements)
            important_combinations = [
                # Business Head combinations
                ['Business Head', 'OEM', 'Year_Start'],
                ['Group Business Manager', 'OEM', 'Year_Start'],
                ['Business Manager', 'OEM', 'Year_Start'],
                
                # Channel/Partner combinations
                ['Group Channel Champ', 'Partner', 'Year_Start'],
                ['Channel Champ', 'Partner', 'Year_Start'],
                ['Vertical Champ', 'End Customer', 'Year_Start'],
                
                # OEM/Partner/Customer combinations
                ['OEM', 'Partner', 'End Customer'],
                ['OEM', 'Partner', 'Year_Start'],
                ['OEM', 'End Customer', 'Year_Start'],
                ['Partner', 'End Customer', 'Year_Start'],
                
                # Region combinations
                ['OEM', 'Region', 'Year_Start'],
                ['Partner', 'Region', 'Year_Start'],
                ['End Customer', 'Region', 'Year_Start'],
                
                # Channel combinations
                ['Channel', 'Year_Start', 'Region'],
                ['Channel', 'Region', 'Year_Start']
            ]
            
            for combo in important_combinations:
                if all(dim in self.df.columns for dim in combo):
                    key = "_".join(combo)
                    grouped = self.df.groupby(combo).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

            # Ensure key combinations include Region
            key_combinations = [
                ['Channel', 'Vertical', 'Region'],
                ['Partner', 'End Customer', 'Region'],
                ['OEM', 'Region', 'Year_Start'],
                # Add more as needed
            ]
            
            for combo in key_combinations:
                if all(col in self.df.columns for col in combo):
                    key = "_".join(combo)
                    grouped = self.df.groupby(combo).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).reset_index()
                    self.dimension_combinations[key] = grouped

            print(f"✅ Created {len(self.dimension_combinations)} dimension combinations")

        except Exception as e:
            print(f"⚠️ Warning: Could not create dimension combinations: {e}")

    def create_comparison_metrics(self):
        """Create year-over-year comparison metrics"""
        try:
            years = sorted(self.yearly_stats.keys())
            if len(years) < 2:
                return

            self.yearly_stats['comparisons'] = {}

            for i in range(1, len(years)):
                current_year = years[i]
                previous_year = years[i-1]

                current_data = self.yearly_stats[current_year]
                previous_data = self.yearly_stats[previous_year]

                # Calculate growth rates
                revenue_growth = ((current_data['total_revenue'] - previous_data['total_revenue']) /
                                previous_data['total_revenue'] * 100) if previous_data['total_revenue'] > 0 else 0

                margin_growth = ((current_data['total_gross_margin'] - previous_data['total_gross_margin']) /
                               previous_data['total_gross_margin'] * 100) if previous_data['total_gross_margin'] > 0 else 0

                transaction_growth = ((current_data['total_transactions'] - previous_data['total_transactions']) /
                                    previous_data['total_transactions'] * 100) if previous_data['total_transactions'] > 0 else 0

                self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}'] = {
                    'revenue_growth': revenue_growth,
                    'margin_growth': margin_growth,
                    'transaction_growth': transaction_growth,
                    'revenue_difference': current_data['total_revenue'] - previous_data['total_revenue'],
                    'margin_difference': current_data['total_gross_margin'] - previous_data['total_gross_margin'],
                    'transaction_difference': current_data['total_transactions'] - previous_data['total_transactions']
                }

                # Add channel comparison
                if 'channel_revenue' in current_data and 'channel_revenue' in previous_data:
                    channel_comparison = {}
                    for channel in current_data['channel_revenue'].keys():
                        if channel in previous_data['channel_revenue']:
                            current_val = current_data['channel_revenue'][channel]
                            prev_val = previous_data['channel_revenue'][channel]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            channel_comparison[channel] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['channel_comparison'] = channel_comparison

                # Add region comparison
                if 'region_revenue' in current_data and 'region_revenue' in previous_data:
                    region_comparison = {}
                    for region in current_data['region_revenue'].keys():
                        if region in previous_data['region_revenue']:
                            current_val = current_data['region_revenue'][region]
                            prev_val = previous_data['region_revenue'][region]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            region_comparison[region] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['region_comparison'] = region_comparison

                # Add partner comparison
                if 'partner_revenue' in current_data and 'partner_revenue' in previous_data:
                    partner_comparison = {}
                    for partner in current_data['partner_revenue'].keys():
                        if partner in previous_data['partner_revenue']:
                            current_val = current_data['partner_revenue'][partner]
                            prev_val = previous_data['partner_revenue'][partner]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            partner_comparison[partner] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['partner_comparison'] = partner_comparison

                # Add OEM comparison
                if 'oem_revenue' in current_data and 'oem_revenue' in previous_data:
                    oem_comparison = {}
                    for oem in current_data['oem_revenue'].keys():
                        if oem in previous_data['oem_revenue']:
                            current_val = current_data['oem_revenue'][oem]
                            prev_val = previous_data['oem_revenue'][oem]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            oem_comparison[oem] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['oem_comparison'] = oem_comparison

                # Add vertical comparison
                if 'vertical_revenue' in current_data and 'vertical_revenue' in previous_data:
                    vertical_comparison = {}
                    for vertical in current_data['vertical_revenue'].keys():
                        if vertical in previous_data['vertical_revenue']:
                            current_val = current_data['vertical_revenue'][vertical]
                            prev_val = previous_data['vertical_revenue'][vertical]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            vertical_comparison[vertical] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['vertical_comparison'] = vertical_comparison

                # Add customer comparison
                if 'customer_revenue' in current_data and 'customer_revenue' in previous_data:
                    customer_comparison = {}
                    for customer in current_data['customer_revenue'].keys():
                        if customer in previous_data['customer_revenue']:
                            current_val = current_data['customer_revenue'][customer]
                            prev_val = previous_data['customer_revenue'][customer]
                            growth = ((current_val - prev_val) / prev_val * 100) if prev_val > 0 else 0
                            customer_comparison[customer] = {
                                'growth': growth,
                                'difference': current_val - prev_val
                            }
                    self.yearly_stats['comparisons'][f'{previous_year}_to_{current_year}']['customer_comparison'] = customer_comparison

        except Exception as e:
            print(f"⚠️ Warning: Could not create comparison metrics: {e}")

    def create_indexes(self):
        """Create indexes for faster searching"""
        # Sort by commonly queried columns
        if 'A/R Posting Date' in self.df.columns:
            self.df = self.df.sort_values('A/R Posting Date')

class SalesChatbot:
    def __init__(self, data_processor):
        self.processor = data_processor
        self.df = data_processor.df
        self.stats = data_processor.summary_stats
        self.yearly_stats = data_processor.yearly_stats
        self.dimension_combinations = data_processor.dimension_combinations
        self.partner_stats = data_processor.partner_stats
        self.oem_stats = data_processor.oem_stats
        self.partner_customer_stats = data_processor.partner_customer_stats
        self.vertical_stats = data_processor.vertical_stats  # NEW: Vertical stats
        self.customer_stats = data_processor.customer_stats  # NEW: End customer stats


    def get_yearly_regional_performance_table(self, year_string):
            """
            Generates a formatted regional performance summary for a given year with Top N filter in HTML table format.
            """
            try:
                # 1. Parse Year String
                if '-' not in year_string:
                    return "❌ Invalid year format. Please use 'YYYY-YY' (e.g., '2022-23')."
                                
                start_year = int(year_string.split('-')[0])
                prev_year = start_year - 1
                
                # 2. Filter Data for Both Years
                current_year_data = self.df[self.df['Year_Start'] == start_year]
                prev_year_data = self.df[self.df['Year_Start'] == prev_year]
                
                if current_year_data.empty:
                    return f"ℹ️ No data available for the year {year_string}."
                
                # 3. Aggregate Regional Stats for Both Years
                current_stats = current_year_data.groupby('Region').agg(
                    TL_Current=('TL Base Value', 'sum'),
                    GM_Current=('Gross Margin Value', 'sum')
                ).reset_index()
                
                prev_stats = prev_year_data.groupby('Region').agg(
                    TL_Prev=('TL Base Value', 'sum'),
                    GM_Prev=('Gross Margin Value', 'sum')
                ).reset_index()
                
                # 4. Merge Data and Fill Missing Values
                if not prev_stats.empty:
                    combined_data = pd.merge(current_stats, prev_stats, on='Region', how='left')
                else:
                    combined_data = current_stats
                    combined_data['TL_Prev'] = 0
                    combined_data['GM_Prev'] = 0
                                
                combined_data = combined_data.fillna(0)
                
                # 5. Calculate derived metrics
                combined_data['GM_Percent'] = (combined_data['GM_Current'] / combined_data['TL_Current'] * 100).round(1)
                combined_data['TL_Growth'] = combined_data.apply(lambda row: 
                    f"{((row['TL_Current'] - row['TL_Prev']) / row['TL_Prev'] * 100):+.1f}%" if row['TL_Prev'] > 0 else "New", axis=1)
                combined_data['GM_Growth'] = combined_data.apply(lambda row: 
                    f"{((row['GM_Current'] - row['GM_Prev']) / row['GM_Prev'] * 100):+.1f}%" if row['GM_Prev'] > 0 else "New", axis=1)
                
                # Convert to Cr for display
                combined_data['TL_Cr'] = (combined_data['TL_Current'] / 10000000).round(2)
                combined_data['GM_Cr'] = (combined_data['GM_Current'] / 10000000).round(2)
                
                # Reorder regions and add missing ones with zero values
                regions_order = ['NORTH', 'SOUTH', 'WEST', 'HO', 'KNY']
                regional_summary = []
                
                for region in regions_order:
                    region_data = combined_data[combined_data['Region'] == region]
                    if not region_data.empty:
                        regional_summary.append(region_data.iloc[0])
                    else:
                        # Add missing region with zeros
                        regional_summary.append({
                            'Region': region, 'TL_Cr': 0.00, 'GM_Cr': 0.00, 
                            'GM_Percent': 0.0, 'TL_Growth': 'No Data', 'GM_Growth': 'No Data'
                        })
                
                regional_df = pd.DataFrame(regional_summary)
                
                # Add totals row
                total_tl = combined_data['TL_Current'].sum()
                total_gm = combined_data['GM_Current'].sum()
                total_row = {
                    'Region': 'TOTAL',
                    'TL_Cr': round(total_tl / 10000000, 2),
                    'GM_Cr': round(total_gm / 10000000, 2),
                    'GM_Percent': round((total_gm / total_tl * 100) if total_tl > 0 else 0, 1),
                    'TL_Growth': 'N/A',
                    'GM_Growth': 'N/A'
                }
                regional_df = pd.concat([regional_df, pd.DataFrame([total_row])], ignore_index=True)
                
                # Format the final regional table
                regional_table = regional_df[['Region', 'TL_Cr', 'GM_Cr', 'GM_Percent', 'TL_Growth', 'GM_Growth']].copy()
                regional_table.columns = ['Region', 'TL (₹Cr)', 'GM (₹Cr)', 'GM%', 'TL Growth', 'GM Growth']
                
                # Create unique ID for this year
                year_id = f"year_{year_string.replace('-', '_')}"
                
                # Start building output with Top N filter
                output_text = f"""## REGIONAL PERFORMANCE SUMMARY FOR {year_string}

    <div style="margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: center;">
            <!-- Top N Filter -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <label for="topNSelector_{year_id}" style="font-weight: bold; margin-bottom: 8px; font-size: 14px; color: #495057;">Select Top N:</label>
                <select id="topNSelector_{year_id}" onchange="updateTopNDisplay_{year_id}()" style="padding: 10px 15px; border: 1px solid #ced4da; border-radius: 6px; background-color: white; font-size: 14px; min-width: 120px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <option value="5" selected>Top 5</option>
                    <option value="10">Top 10</option>
                    <option value="15">Top 15</option>
                    <option value="20">Top 20</option>
                    <option value="all">Show All</option>
                </select>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <span style="font-size: 12px; color: #6c757d; font-style: italic;">
                Top N filter applies to OEMs, Partners, End Customers, Vertical Accounts, and Channels tables.
            </span>
        </div>
    </div>

    <script>
    function updateTopNDisplay_{year_id}() {{
        const selector = document.getElementById('topNSelector_{year_id}');
        const selectedValue = selector.value;
        
        // Get all tables with class 'dynamic-top-n-{year_id}'
        const tables = document.querySelectorAll('table.dynamic-top-n-{year_id}');
        
        tables.forEach(table => {{
            const tbody = table.querySelector('tbody');
            const rows = tbody.querySelectorAll('tr');
            
            if (selectedValue === 'all') {{
                // Show all rows
                rows.forEach(row => row.style.display = '');
            }} else {{
                const topN = parseInt(selectedValue);
                // Show/hide rows based on selection
                rows.forEach((row, index) => {{
                    if (index < topN) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }});
            }}
            
            // Update table titles
            const titleElement = table.closest('div').querySelector('.table-title-dynamic-{year_id}');
            if (titleElement) {{
                const originalTitle = titleElement.getAttribute('data-original-title');
                if (originalTitle) {{
                    if (selectedValue === 'all') {{
                        titleElement.textContent = originalTitle.replace(/TOP \\d+/, 'ALL');
                    }} else {{
                        titleElement.textContent = originalTitle.replace(/TOP \\d+|ALL/, `TOP ${{selectedValue}}`);
                    }}
                }}
            }}
        }});
    }}

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {{
        updateTopNDisplay_{year_id}();
    }});

    // Also run after a short delay to ensure all content is loaded
    setTimeout(function() {{
        updateTopNDisplay_{year_id}();
    }}, 100);
    </script>

    """
                
                # Generate HTML table for regional data (static - no filter)
                regional_html = self._generate_html_table(
                    regional_table,
                    table_id="regional_performance",
                    title="Regional Performance Summary",
                    highlight_total=True
                )
                output_text += regional_html + "\n\n"
                
                # Helper function with HTML table generation and Top N support
                def get_top_performers_table(group_column, title, top_n=5):
                    try:
                        # Check if column exists
                        if group_column not in current_year_data.columns:
                            return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n❌ Column '{group_column}' not found\n\n"
                        
                        # Enhanced data filtering with multiple fallback strategies
                        def filter_valid_data(df, column):
                            """Apply multiple filtering strategies to get valid data"""
                            original_count = len(df)
                            
                            # Strategy 1: Basic null filtering
                            filtered_df = df[df[column].notna()].copy()
                            
                            # Strategy 2: Remove empty strings and whitespace
                            if filtered_df[column].dtype == 'object':
                                filtered_df = filtered_df[filtered_df[column].astype(str).str.strip() != '']
                                
                                # Strategy 3: Remove common placeholder values but keep '-' for verticals
                                if 'vertical' not in title.lower():
                                    placeholder_values = ['nan', 'none', 'null', 'n/a', 'na', '-', 'unknown', 'tbd', 'tba', '']
                                    filtered_df = filtered_df[~filtered_df[column].astype(str).str.lower().str.strip().isin(placeholder_values)]
                            
                            # Strategy 4: If we lost too much data, be more lenient
                            if len(filtered_df) < original_count * 0.1:  # If we have less than 10% of original data
                                print(f"⚠️ Strict filtering removed too much data for {title}, applying lenient filtering")
                                filtered_df = df[df[column].notna()].copy()
                                if filtered_df[column].dtype == 'object':
                                    filtered_df = filtered_df[filtered_df[column].astype(str).str.strip() != '']
                            
                            return filtered_df
                        
                        # Apply filtering
                        current_filtered = filter_valid_data(current_year_data, group_column)
                        
                        if current_filtered.empty:
                            return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n⚠️ No valid data available after filtering\n\n"
                        
                        # Current year stats with error handling - Get ALL records for dynamic tables
                        try:
                            current_stats = current_filtered.groupby(group_column).agg(
                                TL_Current=('TL Base Value', 'sum'),
                                GM_Current=('Gross Margin Value', 'sum')
                            ).reset_index()
                            
                            # Handle potential aggregation errors
                            current_stats = current_stats.dropna()
                            current_stats = current_stats[current_stats['TL_Current'] > 0]  # Remove zero values
                            
                            if current_stats.empty:
                                return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n⚠️ No valid aggregated data found\n\n"
                            
                            current_stats = current_stats.sort_values('TL_Current', ascending=False)
                            
                        except Exception as agg_error:
                            return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n❌ Aggregation failed: {str(agg_error)}\n\n"
                        
                        # DON'T limit to top N here - we need all data for dynamic filtering
                        # if top_n < 999:
                        #     current_stats = current_stats.head(top_n)
                        
                        # Previous year stats for growth calculation with error handling
                        merged_stats = current_stats.copy()
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        
                        if not prev_year_data.empty and group_column in prev_year_data.columns:
                            try:
                                prev_filtered = filter_valid_data(prev_year_data, group_column)
                                if not prev_filtered.empty:
                                    prev_stats = prev_filtered.groupby(group_column).agg(
                                        TL_Prev=('TL Base Value', 'sum'),
                                        GM_Prev=('Gross Margin Value', 'sum')
                                    ).reset_index()
                                    
                                    # Clean previous year data
                                    prev_stats = prev_stats.dropna()
                                    
                                    # Merge with current stats
                                    merged_stats = pd.merge(current_stats, prev_stats, on=group_column, how='left')
                            except Exception as prev_error:
                                print(f"⚠️ Previous year processing failed for {title}: {str(prev_error)}")
                        
                        merged_stats = merged_stats.fillna(0)
                        
                        # Calculate metrics with error handling
                        try:
                            merged_stats['TL_Cr'] = (merged_stats['TL_Current'] / 10000000).round(2)
                            merged_stats['GM_Cr'] = (merged_stats['GM_Current'] / 10000000).round(2)
                            
                            # Safe division for GM percentage
                            merged_stats['GM_Percent'] = merged_stats.apply(
                                lambda row: round((row['GM_Current'] / row['TL_Current'] * 100), 1) if row['TL_Current'] > 0 else 0.0, 
                                axis=1
                            )
                            
                            # Safe division for contributions
                            merged_stats['TL_Contribution'] = merged_stats.apply(
                                lambda row: round((row['TL_Current'] / total_tl * 100), 1) if total_tl > 0 else 0.0,
                                axis=1
                            )
                            merged_stats['GM_Contribution'] = merged_stats.apply(
                                lambda row: round((row['GM_Current'] / total_gm * 100), 1) if total_gm > 0 else 0.0,
                                axis=1
                            )
                            
                            # Safe growth calculations
                            def safe_growth_calc(current, previous):
                                try:
                                    if previous > 0:
                                        return f"{((current - previous) / previous * 100):+.1f}%"
                                    elif current > 0:
                                        return "New"
                                    else:
                                        return "0.0%"
                                except:
                                    return "N/A"
                            
                            merged_stats['TL_Growth'] = merged_stats.apply(
                                lambda row: safe_growth_calc(row['TL_Current'], row['TL_Prev']), axis=1
                            )
                            merged_stats['GM_Growth'] = merged_stats.apply(
                                lambda row: safe_growth_calc(row['GM_Current'], row['GM_Prev']), axis=1
                            )
                            
                        except Exception as calc_error:
                            print(f"⚠️ Calculation error for {title}: {str(calc_error)}")
                            return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n❌ Calculation failed: {str(calc_error)}\n\n"
                        
                        # Prepare display data
                        try:
                            # Handle long names by truncating smartly
                            merged_stats[group_column] = merged_stats[group_column].astype(str).apply(
                                lambda x: x[:25] + "..." if len(str(x)) > 28 else str(x)
                            )
                            
                            # Select and rename columns for display
                            display_cols = [group_column, 'TL_Cr', 'GM_Cr', 'GM_Percent', 'TL_Contribution', 'GM_Contribution', 'TL_Growth', 'GM_Growth']
                            display_df = merged_stats[display_cols].copy()
                            display_df.columns = ['Name', 'TL (₹Cr)', 'GM (₹Cr)', 'GM%', 'TL Cont%', 'GM Cont%', 'TL Growth', 'GM Growth']
                            
                        except Exception as format_error:
                            print(f"⚠️ Formatting error for {title}: {str(format_error)}")
                            return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n❌ Formatting failed: {str(format_error)}\n\n"
                        
                        # Generate HTML table
                        try:
                            section_text = f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n\n"
                            
                            if not display_df.empty:
                                # Generate dynamic HTML table with Top N functionality
                                table_html = generate_dynamic_html_table(
                                    display_df,
                                    table_id=f"{title.lower().replace(' ', '_')}_performance",
                                    title=f"TOP {top_n} {title}",
                                    year_id=year_id
                                )
                                section_text += table_html + "\n\n"
                            else:
                                section_text += "No data to display\n\n"
                            
                            return section_text
                            
                        except Exception as output_error:
                            print(f"⚠️ Output generation error for {title}: {str(output_error)}")
                            # Ultimate fallback
                            section_text = f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n"
                            section_text += "❌ Table formatting failed\n\n"
                            return section_text
                        
                    except Exception as e:
                        print(f"❌ Error in get_top_performers_table for {title}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        return f"### TOP {top_n if top_n < 999 else 'ALL'} {title.upper()}\n❌ Processing failed: {str(e)}\n\n"
                
                # Custom HTML table generator for dynamic tables
                def generate_dynamic_html_table(df, table_id, title, year_id):
                    """Generate HTML table with dynamic top N functionality"""
                    
                    html = f"""
    <div style="margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; font-weight: bold; text-align: center;">
            <span class="table-title-dynamic-{year_id}" data-original-title="{title}">{title}</span>
        </div>
        <div style="overflow-x: auto;">
            <table class="dynamic-top-n-{year_id}" style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
    """
                    
                    # Add headers
                    for col in df.columns:
                        html += f'<th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057;">{col}</th>'
                    
                    html += """
                    </tr>
                </thead>
                <tbody>
    """
                    
                    # Add data rows with initial display logic for Top 5
                    for idx, row in df.iterrows():
                        # Hide rows beyond index 4 (Top 5) by default
                        row_style = '' if idx < 5 else 'display: none;'
                        html += f'<tr style="{row_style}">'
                        
                        for col in df.columns:
                            cell_value = str(row[col])
                            cell_style = "padding: 10px 8px; border-bottom: 1px solid #dee2e6;"
                            
                            # Add color coding for growth values
                            if 'Growth' in col and cell_value not in ['N/A', 'New', 'No Data']:
                                if cell_value.startswith('+'):
                                    cell_style += " color: #28a745; font-weight: 500;"  # Green for positive
                                elif cell_value.startswith('-'):
                                    cell_style += " color: #dc3545; font-weight: 500;"  # Red for negative
                            
                            html += f'<td style="{cell_style}">{cell_value}</td>'
                        
                        html += '</tr>'
                    
                    html += """
                </tbody>
            </table>
        </div>
    </div>
    """
                    
                    return html
                
                # Get available columns with comprehensive search
                available_columns = list(current_year_data.columns)
                
                # Find column mappings with multiple patterns and fuzzy matching
                def find_column_with_patterns(patterns, available_cols):
                    """Find column using multiple pattern matching strategies"""
                    for pattern in patterns:
                        # Exact match (case insensitive)
                        for col in available_cols:
                            if pattern.lower() == col.lower():
                                return col
                        
                        # Contains match
                        for col in available_cols:
                            if pattern.lower() in col.lower() or col.lower() in pattern.lower():
                                return col
                    
                    return None
                
                # Enhanced column mapping
                oem_column = find_column_with_patterns(['OEM', 'Vendor', 'Manufacturer', 'Brand'], available_columns)
                partner_column = find_column_with_patterns(['Partner', 'Reseller', 'Distributor', 'Channel Partner', 'System Integrator'], available_columns)
                end_customer_column = find_column_with_patterns(['End Customer Name', 'End Customer', 'Customer Name', 'Customer', 'Client', 'End Customer (Biz)'], available_columns)
                vertical_column = find_column_with_patterns(['Vertical Account', 'Vertical', 'Vertical Champ', 'Industry'], available_columns)
                channel_column = find_column_with_patterns(['Channel', 'Sales Channel', 'Channel Type'], available_columns)
                
                # Add performance tables with Top N filter (5 is the default display, but all data is loaded)
                if oem_column:
                    output_text += get_top_performers_table(oem_column, 'OEMs', 5)
                else:
                    output_text += "### TOP OEMS\n❌ OEM column not found. Available columns: " + ", ".join(available_columns[:10]) + "...\n\n"
                    
                if partner_column:
                    output_text += get_top_performers_table(partner_column, 'Partners', 5)
                else:
                    output_text += "### TOP ARTNERS\n❌ Partner column not found. Available columns: " + ", ".join(available_columns[:10]) + "...\n\n"
                    
                if end_customer_column:
                    output_text += get_top_performers_table(end_customer_column, 'End Customers', 5)
                else:
                    output_text += "### TOP END CUSTOMERS\n❌ End Customer column not found. Available columns: " + ", ".join(available_columns[:10]) + "...\n\n"
                    
                if vertical_column:
                    output_text += get_top_performers_table(vertical_column, 'Vertical Accounts', 5)
                else:
                    output_text += "### TOP VERTICAL ACCOUNTS\n❌ Vertical Account column not found. Available columns: " + ", ".join(available_columns[:10]) + "...\n\n"
                    
                if channel_column:
                    output_text += get_top_performers_table(channel_column, 'Channels', 5)
                else:
                    output_text += "### TOP CHANNELS\n❌ Channel column not found. Available columns: " + ", ".join(available_columns[:10]) + "...\n\n"
                
                return output_text
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ CRITICAL ERROR: {str(e)}")
                print("Full traceback:")
                print(error_details)
                return f"❌ An error occurred while generating the regional performance table: {str(e)}\n\nDebug info: Check console for full traceback."

    def _generate_html_table(self, df, table_id="data_table", title="Data Table", highlight_total=False):
        """
        Helper method to generate properly formatted HTML tables
        """
        try:
            if df.empty:
                return f"<div class='table-container'><p>No data available for {title}</p></div>"
            
            # Start HTML table
            html = f"""
            <div class="table-container" style="margin: 20px 0; overflow-x: auto;">
                <table class="data-table" id="{table_id}" style="
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 10px 0; 
                    font-size: 14px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                ">
                    <thead>
                        <tr style="
                            background: linear-gradient(135deg, #10a37f 0%, #0e8f6f 100%);
                            color: white;
                            font-weight: 600;
                        ">
            """
            
            # Add headers
            for col in df.columns:
                html += f'<th style="padding: 12px 8px; text-align: left; border-right: 1px solid rgba(255,255,255,0.2);">{col}</th>'
            
            html += "</tr></thead><tbody>"
            
            # Add data rows
            for index, row in df.iterrows():
                # Check if this is the total row for highlighting
                is_total_row = highlight_total and (
                    str(row.iloc[0]).upper() == 'TOTAL' or 
                    'total' in str(row.iloc[0]).lower()
                )
                
                row_style = ""
                if is_total_row:
                    row_style = "background-color: #f8f9fa; font-weight: 600; border-top: 2px solid #10a37f;"
                elif index % 2 == 0:
                    row_style = "background-color: #ffffff;"
                else:
                    row_style = "background-color: #f8f9fa;"
                
                html += f'<tr style="{row_style}">'
                
                for col_index, value in enumerate(row):
                    # Format numeric values
                    formatted_value = self._format_table_value(value, col_index, df.columns[col_index])
                    
                    cell_style = "padding: 10px 8px; border-right: 1px solid #e5e7eb; text-align: "
                    
                    # Align numeric columns to right, text to left
                    if col_index == 0:  # First column (names)
                        cell_style += "left;"
                    else:
                        cell_style += "right;"
                    
                    # Add color coding for growth values
                    if 'Growth' in df.columns[col_index] and formatted_value not in ['N/A', 'New', 'No Data']:
                        if '+' in str(formatted_value):
                            cell_style += " color: #10a37f; font-weight: 600;"
                        elif '-' in str(formatted_value):
                            cell_style += " color: #ef4444; font-weight: 600;"
                    
                    html += f'<td style="{cell_style}">{formatted_value}</td>'
                
                html += "</tr>"
            
            html += """
                    </tbody>
                </table>
            </div>
            """
            
            return html
            
        except Exception as e:
            print(f"Error generating HTML table: {str(e)}")
            return f"<div class='error'>Error generating table: {str(e)}</div>"

    def _format_table_value(self, value, col_index, col_name):
        """
        Helper method to format table values appropriately
        """
        try:
            # Handle None/NaN values
            if pd.isna(value) or value is None:
                return "0.00"
            
            # Convert to string for processing
            str_value = str(value)
            
            # Handle percentage columns
            if '%' in col_name or 'Percent' in col_name:
                try:
                    float_val = float(str_value.replace('%', ''))
                    return f"{float_val:.1f}%"
                except:
                    return str_value
            
            # Handle currency columns (₹Cr)
            if '₹Cr' in col_name or 'Cr' in col_name:
                try:
                    float_val = float(str_value)
                    return f"₹{float_val:.2f}"
                except:
                    return str_value
            
            # Handle growth columns
            if 'Growth' in col_name:
                if str_value in ['New', 'N/A', 'No Data']:
                    return str_value
                elif '%' in str_value:
                    return str_value  # Already formatted
                else:
                    try:
                        float_val = float(str_value.replace('%', ''))
                        return f"{float_val:+.1f}%"
                    except:
                        return str_value
            
            # For first column (names), truncate if too long
            if col_index == 0:
                if len(str_value) > 30:
                    return str_value[:27] + "..."
                return str_value
            
            # For other numeric columns
            try:
                float_val = float(str_value)
                return f"{float_val:.2f}"
            except:
                return str_value
                
        except Exception as e:
            print(f"Error formatting value {value}: {str(e)}")
            return str(value) if value is not None else "N/A"


    def handle_vertical_champ_customer_query(self, query):
            """Handle queries combining Vertical Champ and End Customer Name performance with various metrics"""
            try:
                query_lower = query.lower()
                
                # Extract Vertical Champ name (case-insensitive)
                vertical_champ = None
                for name in self.df['Vertical Champ'].dropna().unique():
                    if str(name).lower() in query_lower:
                        vertical_champ = name
                        break
                
                if not vertical_champ:
                    available_champs = self.df['Vertical Champ'].dropna().unique()[:5]
                    return f"❌ Specify a Vertical Champ. Available: {', '.join(map(str, available_champs))}"

                # Extract End Customer name (case-insensitive)
                customer = None
                for customer_name in self.df['End Customer Name'].dropna().unique():
                    if str(customer_name).lower() in query_lower:
                        customer = customer_name
                        break

                # Extract year (FY23 or 2023)
                year = None
                year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
                if year_match:
                    year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

                # Filter data
                filtered = self.df[
                    (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                ]
                if customer:
                    filtered = filtered[filtered['End Customer Name'].str.lower() == customer.lower()]
                if year:
                    filtered = filtered[filtered['Year_Start'] == year]

                if filtered.empty:
                    return f"❌ No data for Vertical Champ {vertical_champ}" + \
                        (f" with Customer {customer}" if customer else "") + \
                        (f" in {year}" if year else "")

                # Calculate metrics
                total_revenue = filtered['TL Base Value'].sum()
                total_margin = filtered['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(filtered)

                # Get all customers this vertical champ works with
                all_customers_data = self.df[
                    (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                ]
                if year:
                    all_customers_data = all_customers_data[all_customers_data['Year_Start'] == year]
                
                all_customers = all_customers_data['End Customer Name'].unique()
                customer_count = len(all_customers)

                # Handle different query types
                
                # 1. Simple gross margin query (returns only what's asked)
                if ('gross margin' in query_lower and 'for vertical champ' in query_lower and 
                    'with customer' in query_lower and customer and not 'performance' in query_lower):
                    return f"💹 Gross Margin: {format_in_crores(total_margin)}"
                
                # 2. Gross margin performance (detailed view)
                elif ('gross margin performance' in query_lower or 
                    ('performance' in query_lower and 'gross margin' in query_lower)):
                    result = f"📊 {vertical_champ} × {customer}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

                # 3. List top customers by revenue
                elif ('list top' in query_lower and 'customers by revenue' in query_lower) or \
                    ('top customers by revenue' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    top_customers_list = vc_data.groupby('End Customer Name')['TL Base Value'].sum() \
                                        .sort_values(ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Customers by Revenue for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (customer_name, revenue) in enumerate(top_customers_list.items(), 1):
                        result += f"{i}. {customer_name}: {format_in_crores(revenue)}\n"
                    return result

                # 3a. List top customers by gross margin
                elif ('list top' in query_lower and 'customers by gross margin' in query_lower) or \
                    ('top customers by gross margin' in query_lower) or \
                    ('list top' in query_lower and 'customers by margin' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    # Group by customer and calculate both margin and revenue for GM%
                    customer_metrics = vc_data.groupby('End Customer Name').agg({
                        'Gross Margin Value': 'sum',
                        'TL Base Value': 'sum'
                    })
                    customer_metrics['GM_Percent'] = (customer_metrics['Gross Margin Value'] / customer_metrics['TL Base Value'] * 100)
                    
                    # Sort by gross margin value
                    top_customers_by_margin = customer_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Customers by Gross Margin for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (customer_name, data) in enumerate(top_customers_by_margin.iterrows(), 1):
                        margin = data['Gross Margin Value']
                        revenue = data['TL Base Value']
                        gm_pct = data['GM_Percent']
                        result += f"{i}. {customer_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                    return result

                # 3b. List top customers by contribution
                elif ('list top' in query_lower and 'customers by contribution' in query_lower) or \
                    ('top customers by contribution' in query_lower) or \
                    ('list top' in query_lower and 'contribution' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    # Calculate total revenue for percentage calculation
                    total_vc_revenue = vc_data['TL Base Value'].sum()
                    total_vc_margin = vc_data['Gross Margin Value'].sum()
                    
                    # Group by customer and calculate contribution metrics
                    customer_metrics = vc_data.groupby('End Customer Name').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    
                    # Calculate contribution percentages
                    customer_metrics['Revenue_Contribution'] = (customer_metrics['TL Base Value'] / total_vc_revenue * 100)
                    customer_metrics['Margin_Contribution'] = (customer_metrics['Gross Margin Value'] / total_vc_margin * 100)
                    customer_metrics['GM_Percent'] = (customer_metrics['Gross Margin Value'] / customer_metrics['TL Base Value'] * 100)
                    
                    # Sort by revenue contribution (primary metric for "contribution")
                    top_customers_by_contribution = customer_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Customers by Contribution for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Portfolio: {format_in_crores(total_vc_revenue)} Revenue | {format_in_crores(total_vc_margin)} Margin\n\n"
                    
                    for i, (customer_name, data) in enumerate(top_customers_by_contribution.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        rev_contrib = data['Revenue_Contribution']
                        margin_contrib = data['Margin_Contribution']
                        gm_pct = data['GM_Percent']
                        
                        result += f"{i}. {customer_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                        result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                    
                    return result

                # 3c. New customer acquisitions
                elif ('new customer acquisitions' in query_lower) or \
                    ('new customers' in query_lower and 'acquisitions' in query_lower) or \
                    ('customer acquisitions' in query_lower) or \
                    ('newly acquired customers' in query_lower):
                    
                    # Get current year or use latest available
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    previous_year = current_year - 1
                    
                    # Get customers for current year
                    current_customers = set(self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['End Customer Name'].unique())
                    
                    # Get customers for previous year
                    previous_customers = set(self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                        (self.df['Year_Start'] == previous_year)
                    ]['End Customer Name'].unique())
                    
                    # Find new customers (in current year but not in previous year)
                    new_customers = current_customers - previous_customers
                    
                    if not new_customers:
                        return f"✅ No new customer acquisitions for {vertical_champ} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                    
                    # Get performance data for new customers
                    new_customer_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                        (self.df['Year_Start'] == current_year) &
                        (self.df['End Customer Name'].isin(new_customers))
                    ]
                    
                    # Calculate metrics for new customers
                    new_customer_metrics = new_customer_data.groupby('End Customer Name').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    new_customer_metrics['GM_Percent'] = (new_customer_metrics['Gross Margin Value'] / new_customer_metrics['TL Base Value'] * 100)
                    new_customer_metrics['Transaction_Count'] = new_customer_data.groupby('End Customer Name').size()
                    
                    # Sort by revenue
                    new_customer_metrics = new_customer_metrics.sort_values('TL Base Value', ascending=False)
                    
                    # Calculate totals
                    total_new_revenue = new_customer_metrics['TL Base Value'].sum()
                    total_new_margin = new_customer_metrics['Gross Margin Value'].sum()
                    total_new_transactions = new_customer_metrics['Transaction_Count'].sum()
                    avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                    
                    result = f"🆕 New Customer Acquisitions for {vertical_champ} in FY{str(current_year)[2:]}:\n"
                    result += f"📊 Total Impact: {len(new_customers)} new customers\n"
                    result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                    result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                    result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                    
                    result += f"🔍 Individual Performance:\n"
                    for i, (customer_name, data) in enumerate(new_customer_metrics.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = data['GM_Percent']
                        transactions = data['Transaction_Count']
                        
                        result += f"{i}. {customer_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)}\n"
                        result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                        result += f"   • Transactions: {transactions:,}\n\n"
                    
                    return result

                # 4. What customers does Vertical Champ manage
                elif ('what customers does' in query_lower and 'manage' in query_lower) or \
                    ('customers managed' in query_lower) or ('customers handled' in query_lower):
                    
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    all_customers_with_revenue = vc_data.groupby('End Customer Name')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    result = f"🏢 Customers managed by {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {len(all_customers_with_revenue)} customers\n\n"
                    
                    if len(all_customers_with_revenue) == 0:
                        return f"❌ No customer data found for {vertical_champ}"
                    
                    # Show ALL customers, not just top 5
                    result += "🔝 All Customers by Revenue:\n"
                    for i, (customer_name, revenue) in enumerate(all_customers_with_revenue.items(), 1):
                        result += f"{i}. {customer_name}: {format_in_crores(revenue)}\n"
                    
                    return result

                # 5. Show revenue for Vertical Champ (simple revenue query)
                elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                    result = f"💰 Revenue for {vertical_champ}"
                    if customer:
                        result += f" with Customer {customer}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(total_revenue)}"
                    return result
                
                # 6. Gross margin across all customers
                elif 'gross margin' in query_lower and 'across all customers' in query_lower:
                    all_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        all_data = all_data[all_data['Year_Start'] == year]
                    
                    all_margin = all_data['Gross Margin Value'].sum()
                    all_revenue = all_data['TL Base Value'].sum()
                    all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                    
                    result = f"💹 Gross Margin for {vertical_champ} across all customers"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                    return result
                    
                # 7. Compare YoY growth
                elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                    if not year:
                        return "❌ Please specify a year for YoY comparison"
                    
                    prev_year = year - 1
                    prev_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if customer:
                        prev_data = prev_data[prev_data['End Customer Name'].str.lower() == customer.lower()]
                    prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                    
                    if prev_data.empty:
                        return f"❌ No data available for previous year {prev_year} to compare"
                    
                    prev_revenue = prev_data['TL Base Value'].sum()
                    prev_margin = prev_data['Gross Margin Value'].sum()
                    prev_count = len(prev_data)
                    
                    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                    margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                    count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                    
                    result = f"📈 YoY Growth for {vertical_champ}"
                    if customer:
                        result += f" with Customer {customer}"
                    result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {count_growth:+.1f}%"
                    
                    result += f"\n\nActual Figures:\n"
                    result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                    result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                    
                    return result
                
                # 8. Highest margin customer
                elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    customer_margins = vc_data.groupby('End Customer Name')['Gross Margin Value'].sum() \
                                        .sort_values(ascending=False)
                    
                    if customer_margins.empty:
                        return f"❌ No margin data available for {vertical_champ}"
                    
                    top_customer = customer_margins.index[0]
                    top_margin = customer_margins.iloc[0]
                    total_all_margin = vc_data['Gross Margin Value'].sum()
                    top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                    
                    result = f"🏆 Highest Margin Customer for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {top_customer}\n"
                    result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                    result += f"   • Contribution: {top_percent:.1f}% of total margin"
                    return result
                
                # 9. Customer contribution mix
                elif 'customer contribution' in query_lower or 'customer mix' in query_lower or 'contribution mix' in query_lower:
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    customer_revenues = vc_data.groupby('End Customer Name')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    if len(customer_revenues) == 0:
                        return f"❌ No customer data found for {vertical_champ}"
                    
                    total = customer_revenues.sum()
                    result = f"📊 Customer Revenue Mix for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                    
                    for i, (customer_name, revenue) in enumerate(customer_revenues.head(7).items(), 1):
                        percent = (revenue / total * 100) if total > 0 else 0
                        result += f"{i}. {customer_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                    
                    if len(customer_revenues) > 7:
                        result += f"\n+ {len(customer_revenues) - 7} more customers"
                    
                    return result
                
                # 10. Growth potential analysis
                elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                    if not customer:
                        return "❌ Please specify a customer for growth potential analysis"
                    
                    # Get current year data (or latest available)
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    
                    # Get historical data for trend analysis (last 3 years)
                    years_to_analyze = [current_year-2, current_year-1, current_year]
                    historical_data = []
                    
                    for y in years_to_analyze:
                        year_data = self.df[
                            (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                            (self.df['End Customer Name'].str.lower() == customer.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            revenue = year_data['TL Base Value'].sum()
                            margin = year_data['Gross Margin Value'].sum()
                            transactions = len(year_data)
                            gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                            
                            historical_data.append({
                                'year': y,
                                'revenue': revenue,
                                'margin': margin,
                                'transactions': transactions,
                                'gm_percent': gm_pct
                            })
                    
                    if len(historical_data) < 2:
                        return f"❌ Insufficient historical data for growth potential analysis"
                    
                    # Calculate trends
                    recent = historical_data[-1]
                    previous = historical_data[-2]
                    
                    revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                    margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                    transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                    
                    # Get market share within this vertical champ for this customer
                    vc_total = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['TL Base Value'].sum()
                    
                    market_share = (recent['revenue'] / vc_total * 100) if vc_total > 0 else 0
                    
                    result = f"🚀 Growth Potential Analysis: {vertical_champ} × {customer}\n\n"
                    result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                    result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                    result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                    result += f"   • Market Share: {market_share:.1f}% (within VC portfolio)\n"
                    result += f"   • Transactions: {recent['transactions']:,}\n\n"
                    
                    result += f"📈 Growth Trends (YoY):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                    
                    # Growth potential assessment
                    avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                    
                    if avg_growth > 20:
                        potential = "🔥 HIGH - Strong upward trajectory"
                    elif avg_growth > 10:
                        potential = "📈 MODERATE - Steady growth pattern"
                    elif avg_growth > 0:
                        potential = "🔄 LOW - Slow growth"
                    else:
                        potential = "⚠️ DECLINING - Needs attention"
                    
                    result += f"💡 Growth Potential: {potential}\n\n"
                    
                    # Historical trend
                    result += f"📅 3-Year Trend:\n"
                    for data in historical_data:
                        result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                        result += f"(GM: {data['gm_percent']:.1f}%)\n"
                    
                    return result
                
                # 11. Customer performance trend
                elif 'customer performance trend' in query_lower or 'customer trend' in query_lower or 'trend' in query_lower:
                    if not year:
                        year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                    
                    # Get data for last 3 years
                    years = [year-2, year-1, year]
                    trend_data = []
                    
                    for y in years:
                        year_data = self.df[
                            (self.df['Vertical Champ'].str.lower() == vertical_champ.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            customer_year = year_data.groupby('End Customer Name')['TL Base Value'].sum().nlargest(3).to_dict()
                            total_year_revenue = year_data['TL Base Value'].sum()
                            trend_data.append({
                                'year': y,
                                'top_customers': customer_year,
                                'total_revenue': total_year_revenue
                            })
                    
                    if len(trend_data) < 2:
                        return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                    
                    result = f"📈 Customer Performance Trend for {vertical_champ}:\n\n"
                    for entry in trend_data:
                        result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                        for i, (customer_name, revenue) in enumerate(entry['top_customers'].items(), 1):
                            result += f"   {i}. {customer_name}: {format_in_crores(revenue)}\n"
                        result += "\n"
                    
                    return result
                
                # 12. Customer dependency analysis
                elif 'customer dependency' in query_lower or 'dependency' in query_lower:
                    vc_data = self.df[
                        (self.df['Vertical Champ'].str.lower() == vertical_champ.lower())
                    ]
                    if year:
                        vc_data = vc_data[vc_data['Year_Start'] == year]
                    
                    customer_revenues = vc_data.groupby('End Customer Name')['TL Base Value'].sum().sort_values(ascending=False)
                    total_revenue_vc = customer_revenues.sum()
                    
                    if len(customer_revenues) == 0:
                        return f"❌ No customer data found for {vertical_champ}"
                    
                    top_customer_share = (customer_revenues.iloc[0] / total_revenue_vc * 100) if total_revenue_vc > 0 else 0
                    top_3_share = (customer_revenues.head(3).sum() / total_revenue_vc * 100) if total_revenue_vc > 0 else 0
                    
                    result = f"⚖️ Customer Dependency Analysis for {vertical_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"📊 Concentration Risk:\n"
                    result += f"   • Top Customer Share: {top_customer_share:.1f}%\n"
                    result += f"   • Top 3 Customers Share: {top_3_share:.1f}%\n"
                    result += f"   • Total Customers: {len(customer_revenues)}\n\n"
                    
                    # Risk assessment
                    if top_customer_share > 50:
                        risk_level = "🔴 HIGH"
                    elif top_customer_share > 30:
                        risk_level = "🟡 MEDIUM"
                    else:
                        risk_level = "🟢 LOW"
                    
                    result += f"Risk Level: {risk_level} dependency\n\n"
                    result += f"Top Customer: {customer_revenues.index[0]} ({top_customer_share:.1f}%)"
                    
                    return result
                
                # 13. Customer benchmark analysis
                elif 'customer benchmark' in query_lower or 'benchmark' in query_lower:
                    if not customer:
                        return "❌ Please specify a customer for benchmarking"
                    
                    # Get performance of this customer across all vertical champs
                    customer_data = self.df[self.df['End Customer Name'].str.lower() == customer.lower()]
                    if year:
                        customer_data = customer_data[customer_data['Year_Start'] == year]
                    
                    vc_performance = customer_data.groupby('Vertical Champ').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).sort_values('TL Base Value', ascending=False)
                    
                    if vc_performance.empty:
                        return f"❌ No data found for Customer {customer}"
                    
                    # Find rank of current vertical champ
                    current_rank = None
                    for i, vc in enumerate(vc_performance.index, 1):
                        if vc.lower() == vertical_champ.lower():
                            current_rank = i
                            break
                    
                    result = f"🏁 Customer {customer} Benchmark"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"Vertical Champ Ranking (by Revenue):\n"
                    
                    for i, (vc, data) in enumerate(vc_performance.head(5).iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        prefix = "👑" if i == 1 else f"{i}."
                        highlight = " ← YOU" if vc.lower() == vertical_champ.lower() else ""
                        
                        result += f"{prefix} {vc}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                    
                    if current_rank and current_rank > 5:
                        result += f"\n{vertical_champ} ranks #{current_rank} for {customer}"
                    
                    return result

                # Default case - show basic performance metrics
                else:
                    result = f"📊 {vertical_champ}"
                    if customer:
                        result += f" × {customer}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

            except Exception as e:
                return f"❌ Error processing query: {str(e)}"


    def handle_channel_champ_partner_query(self, query):
            """Handle queries combining Channel Champ and Partner performance with various metrics"""
            try:
                query_lower = query.lower()
                
                # Extract Channel Champ (case-insensitive)
                channel_champ = None
                for name in self.df['Channel Champ'].dropna().unique():
                    if str(name).lower() in query_lower:
                        channel_champ = name
                        break
                
                if not channel_champ:
                    available_champs = self.df['Channel Champ'].dropna().unique()[:5]
                    return f"❌ Specify a Channel Champ. Available: {', '.join(map(str, available_champs))}"

                # Extract Partner name (case-insensitive)
                partner = None
                for partner_name in self.df['Partner'].dropna().unique():
                    if str(partner_name).lower() in query_lower:
                        partner = partner_name
                        break

                # Extract year (FY23 or 2023)
                year = None
                year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
                if year_match:
                    year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

                # Filter data
                filtered = self.df[
                    (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                ]
                if partner:
                    filtered = filtered[filtered['Partner'].str.lower() == partner.lower()]
                if year:
                    filtered = filtered[filtered['Year_Start'] == year]

                if filtered.empty:
                    return f"❌ No data for Channel Champ {channel_champ}" + \
                        (f" with Partner {partner}" if partner else "") + \
                        (f" in {year}" if year else "")

                # Calculate metrics
                total_revenue = filtered['TL Base Value'].sum()
                total_margin = filtered['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(filtered)

                # Get all Partners this channel champ works with
                all_partners_data = self.df[
                    (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                ]
                if year:
                    all_partners_data = all_partners_data[all_partners_data['Year_Start'] == year]
                
                all_partners = all_partners_data['Partner'].unique()
                partner_count = len(all_partners)

                # Handle different query types
                
                # 1. Simple gross margin query (returns only what's asked)
                if ('gross margin' in query_lower and 'for channel champ' in query_lower and 
                    'with partner' in query_lower and partner and not 'performance' in query_lower):
                    return f"💹 Gross Margin: {format_in_crores(total_margin)}"
                
                # 2. Gross margin performance (detailed view)
                elif ('gross margin performance' in query_lower or 
                    ('performance' in query_lower and 'gross margin' in query_lower)):
                    result = f"📊 {channel_champ} × {partner}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

                # 3. List top Partners by revenue
                elif ('list top' in query_lower and 'partners by revenue' in query_lower) or \
                    ('top partners by revenue' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    top_partners_list = cc_data.groupby('Partner')['TL Base Value'].sum() \
                                    .sort_values(ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Revenue for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (partner_name, revenue) in enumerate(top_partners_list.items(), 1):
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)}\n"
                    return result

                # 3a. List top Partners by gross margin
                elif ('list top' in query_lower and 'partners by gross margin' in query_lower) or \
                    ('top partners by gross margin' in query_lower) or \
                    ('list top' in query_lower and 'partners by margin' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    # Group by Partner and calculate both margin and revenue for GM%
                    partner_metrics = cc_data.groupby('Partner').agg({
                        'Gross Margin Value': 'sum',
                        'TL Base Value': 'sum'
                    })
                    partner_metrics['GM_Percent'] = (partner_metrics['Gross Margin Value'] / partner_metrics['TL Base Value'] * 100)
                    
                    # Sort by gross margin value
                    top_partners_by_margin = partner_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Gross Margin for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (partner_name, data) in enumerate(top_partners_by_margin.iterrows(), 1):
                        margin = data['Gross Margin Value']
                        revenue = data['TL Base Value']
                        gm_pct = data['GM_Percent']
                        result += f"{i}. {partner_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                    return result

                # 3b. List top Partners by contribution
                elif ('list top' in query_lower and 'partners by contribution' in query_lower) or \
                    ('top partners by contribution' in query_lower) or \
                    ('list top' in query_lower and 'contribution' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    # Calculate total revenue for percentage calculation
                    total_cc_revenue = cc_data['TL Base Value'].sum()
                    total_cc_margin = cc_data['Gross Margin Value'].sum()
                    
                    # Group by Partner and calculate contribution metrics
                    partner_metrics = cc_data.groupby('Partner').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    
                    # Calculate contribution percentages
                    partner_metrics['Revenue_Contribution'] = (partner_metrics['TL Base Value'] / total_cc_revenue * 100)
                    partner_metrics['Margin_Contribution'] = (partner_metrics['Gross Margin Value'] / total_cc_margin * 100)
                    partner_metrics['GM_Percent'] = (partner_metrics['Gross Margin Value'] / partner_metrics['TL Base Value'] * 100)
                    
                    # Sort by revenue contribution (primary metric for "contribution")
                    top_partners_by_contribution = partner_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Contribution for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Portfolio: {format_in_crores(total_cc_revenue)} Revenue | {format_in_crores(total_cc_margin)} Margin\n\n"
                    
                    for i, (partner_name, data) in enumerate(top_partners_by_contribution.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        rev_contrib = data['Revenue_Contribution']
                        margin_contrib = data['Margin_Contribution']
                        gm_pct = data['GM_Percent']
                        
                        result += f"{i}. {partner_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                        result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                    
                    return result

                # 3c. New Partner acquisitions
                elif ('new partner acquisitions' in query_lower) or \
                    ('new partners' in query_lower and 'acquisitions' in query_lower) or \
                    ('partner acquisitions' in query_lower) or \
                    ('newly acquired partners' in query_lower):
                    
                    # Get current year or use latest available
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    previous_year = current_year - 1
                    
                    # Get Partners for current year
                    current_partners = set(self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['Partner'].unique())
                    
                    # Get Partners for previous year
                    previous_partners = set(self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                        (self.df['Year_Start'] == previous_year)
                    ]['Partner'].unique())
                    
                    # Find new Partners (in current year but not in previous year)
                    new_partners = current_partners - previous_partners
                    
                    if not new_partners:
                        return f"✅ No new Partner acquisitions for {channel_champ} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                    
                    # Get performance data for new Partners
                    new_partner_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year) &
                        (self.df['Partner'].isin(new_partners))
                    ]
                    
                    # Calculate metrics for new Partners
                    new_partner_metrics = new_partner_data.groupby('Partner').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    new_partner_metrics['GM_Percent'] = (new_partner_metrics['Gross Margin Value'] / new_partner_metrics['TL Base Value'] * 100)
                    new_partner_metrics['Transaction_Count'] = new_partner_data.groupby('Partner').size()
                    
                    # Sort by revenue
                    new_partner_metrics = new_partner_metrics.sort_values('TL Base Value', ascending=False)
                    
                    # Calculate totals
                    total_new_revenue = new_partner_metrics['TL Base Value'].sum()
                    total_new_margin = new_partner_metrics['Gross Margin Value'].sum()
                    total_new_transactions = new_partner_metrics['Transaction_Count'].sum()
                    avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                    
                    result = f"🆕 New Partner Acquisitions for {channel_champ} in FY{str(current_year)[2:]}:\n"
                    result += f"📊 Total Impact: {len(new_partners)} new Partners\n"
                    result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                    result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                    result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                    
                    result += f"🔍 Individual Performance:\n"
                    for i, (partner_name, data) in enumerate(new_partner_metrics.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = data['GM_Percent']
                        transactions = data['Transaction_Count']
                        
                        result += f"{i}. {partner_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)}\n"
                        result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                        result += f"   • Transactions: {transactions:,}\n\n"
                    
                    return result

                # 4. What Partners does Channel Champ manage
                elif ('what partners does' in query_lower and 'manage' in query_lower) or \
                    ('partners managed' in query_lower) or ('partners handled' in query_lower):
                    
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    all_partners_with_revenue = cc_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    result = f"🤝 Partners managed by {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {len(all_partners_with_revenue)} Partners\n\n"
                    
                    if len(all_partners_with_revenue) == 0:
                        return f"❌ No Partner data found for {channel_champ}"
                    
                    # Show ALL Partners, not just top 5
                    result += "🔝 All Partners by Revenue:\n"
                    for i, (partner_name, revenue) in enumerate(all_partners_with_revenue.items(), 1):
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)}\n"
                    
                    return result

                # 5. Show revenue for Channel Champ (simple revenue query)
                elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                    result = f"💰 Revenue for {channel_champ}"
                    if partner:
                        result += f" with Partner {partner}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(total_revenue)}"
                    return result
                
                # 6. Gross margin across all Partners
                elif 'gross margin' in query_lower and 'across all partners' in query_lower:
                    all_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        all_data = all_data[all_data['Year_Start'] == year]
                    
                    all_margin = all_data['Gross Margin Value'].sum()
                    all_revenue = all_data['TL Base Value'].sum()
                    all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                    
                    result = f"💹 Gross Margin for {channel_champ} across all Partners"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                    return result
                    
                # 7. Compare YoY growth
                elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                    if not year:
                        return "❌ Please specify a year for YoY comparison"
                    
                    prev_year = year - 1
                    prev_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if partner:
                        prev_data = prev_data[prev_data['Partner'].str.lower() == partner.lower()]
                    prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                    
                    if prev_data.empty:
                        return f"❌ No data available for previous year {prev_year} to compare"
                    
                    prev_revenue = prev_data['TL Base Value'].sum()
                    prev_margin = prev_data['Gross Margin Value'].sum()
                    prev_count = len(prev_data)
                    
                    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                    margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                    count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                    
                    result = f"📈 YoY Growth for {channel_champ}"
                    if partner:
                        result += f" with Partner {partner}"
                    result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {count_growth:+.1f}%"
                    
                    result += f"\n\nActual Figures:\n"
                    result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                    result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                    
                    return result
                
                # 8. Highest margin Partner
                elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    partner_margins = cc_data.groupby('Partner')['Gross Margin Value'].sum() \
                                    .sort_values(ascending=False)
                    
                    if partner_margins.empty:
                        return f"❌ No margin data available for {channel_champ}"
                    
                    top_partner = partner_margins.index[0]
                    top_margin = partner_margins.iloc[0]
                    total_all_margin = cc_data['Gross Margin Value'].sum()
                    top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                    
                    result = f"🏆 Highest Margin Partner for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {top_partner}\n"
                    result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                    result += f"   • Contribution: {top_percent:.1f}% of total margin"
                    return result
                
                # 9. Partner contribution mix
                elif 'partner contribution' in query_lower or 'partner mix' in query_lower or 'contribution mix' in query_lower:
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    partner_revenues = cc_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    if len(partner_revenues) == 0:
                        return f"❌ No Partner data found for {channel_champ}"
                    
                    total = partner_revenues.sum()
                    result = f"📊 Partner Revenue Mix for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                    
                    for i, (partner_name, revenue) in enumerate(partner_revenues.head(7).items(), 1):
                        percent = (revenue / total * 100) if total > 0 else 0
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                    
                    if len(partner_revenues) > 7:
                        result += f"\n+ {len(partner_revenues) - 7} more Partners"
                    
                    return result
                
                # 10. Growth potential analysis
                elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                    if not partner:
                        return "❌ Please specify a Partner for growth potential analysis"
                    
                    # Get current year data (or latest available)
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    
                    # Get historical data for trend analysis (last 3 years)
                    years_to_analyze = [current_year-2, current_year-1, current_year]
                    historical_data = []
                    
                    for y in years_to_analyze:
                        year_data = self.df[
                            (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                            (self.df['Partner'].str.lower() == partner.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            revenue = year_data['TL Base Value'].sum()
                            margin = year_data['Gross Margin Value'].sum()
                            transactions = len(year_data)
                            gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                            
                            historical_data.append({
                                'year': y,
                                'revenue': revenue,
                                'margin': margin,
                                'transactions': transactions,
                                'gm_percent': gm_pct
                            })
                    
                    if len(historical_data) < 2:
                        return f"❌ Insufficient historical data for growth potential analysis"
                    
                    # Calculate trends
                    recent = historical_data[-1]
                    previous = historical_data[-2]
                    
                    revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                    margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                    transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                    
                    # Get market share within this channel champ for this Partner
                    cc_total = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['TL Base Value'].sum()
                    
                    market_share = (recent['revenue'] / cc_total * 100) if cc_total > 0 else 0
                    
                    result = f"🚀 Growth Potential Analysis: {channel_champ} × {partner}\n\n"
                    result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                    result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                    result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                    result += f"   • Market Share: {market_share:.1f}% (within CC portfolio)\n"
                    result += f"   • Transactions: {recent['transactions']:,}\n\n"
                    
                    result += f"📈 Growth Trends (YoY):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                    
                    # Growth potential assessment
                    avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                    
                    if avg_growth > 20:
                        potential = "🔥 HIGH - Strong upward trajectory"
                    elif avg_growth > 10:
                        potential = "📈 MODERATE - Steady growth pattern"
                    elif avg_growth > 0:
                        potential = "🔄 LOW - Slow growth"
                    else:
                        potential = "⚠️ DECLINING - Needs attention"
                    
                    result += f"💡 Growth Potential: {potential}\n\n"
                    
                    # Historical trend
                    result += f"📅 3-Year Trend:\n"
                    for data in historical_data:
                        result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                        result += f"(GM: {data['gm_percent']:.1f}%)\n"
                    
                    return result
                
                # 11. Partner performance trend
                elif 'partner performance trend' in query_lower or 'partner trend' in query_lower or 'trend' in query_lower:
                    if not year:
                        year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                    
                    # Get data for last 3 years
                    years = [year-2, year-1, year]
                    trend_data = []
                    
                    for y in years:
                        year_data = self.df[
                            (self.df['Channel Champ'].str.lower() == channel_champ.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            partner_year = year_data.groupby('Partner')['TL Base Value'].sum().nlargest(3).to_dict()
                            total_year_revenue = year_data['TL Base Value'].sum()
                            trend_data.append({
                                'year': y,
                                'top_partners': partner_year,
                                'total_revenue': total_year_revenue
                            })
                    
                    if len(trend_data) < 2:
                        return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                    
                    result = f"📈 Partner Performance Trend for {channel_champ}:\n\n"
                    for entry in trend_data:
                        result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                        for i, (partner_name, revenue) in enumerate(entry['top_partners'].items(), 1):
                            result += f"   {i}. {partner_name}: {format_in_crores(revenue)}\n"
                        result += "\n"
                    
                    return result
                
                # 12. Partner dependency analysis
                elif 'partner dependency' in query_lower or 'dependency' in query_lower:
                    cc_data = self.df[
                        (self.df['Channel Champ'].str.lower() == channel_champ.lower())
                    ]
                    if year:
                        cc_data = cc_data[cc_data['Year_Start'] == year]
                    
                    partner_revenues = cc_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    total_revenue_cc = partner_revenues.sum()
                    
                    if len(partner_revenues) == 0:
                        return f"❌ No Partner data found for {channel_champ}"
                    
                    top_partner_share = (partner_revenues.iloc[0] / total_revenue_cc * 100) if total_revenue_cc > 0 else 0
                    top_3_share = (partner_revenues.head(3).sum() / total_revenue_cc * 100) if total_revenue_cc > 0 else 0
                    
                    result = f"⚖️ Partner Dependency Analysis for {channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"📊 Concentration Risk:\n"
                    result += f"   • Top Partner Share: {top_partner_share:.1f}%\n"
                    result += f"   • Top 3 Partners Share: {top_3_share:.1f}%\n"
                    result += f"   • Total Partners: {len(partner_revenues)}\n\n"
                    
                    # Risk assessment
                    if top_partner_share > 50:
                        risk_level = "🔴 HIGH"
                    elif top_partner_share > 30:
                        risk_level = "🟡 MEDIUM"
                    else:
                        risk_level = "🟢 LOW"
                    
                    result += f"Risk Level: {risk_level} dependency\n\n"
                    result += f"Top Partner: {partner_revenues.index[0]} ({top_partner_share:.1f}%)"
                    
                    return result
                
                # 13. Partner benchmark analysis
                elif 'partner benchmark' in query_lower or 'benchmark' in query_lower:
                    if not partner:
                        return "❌ Please specify a Partner for benchmarking"
                    
                    # Get performance of this Partner across all channel champs
                    partner_data = self.df[self.df['Partner'].str.lower() == partner.lower()]
                    if year:
                        partner_data = partner_data[partner_data['Year_Start'] == year]
                    
                    cc_performance = partner_data.groupby('Channel Champ').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).sort_values('TL Base Value', ascending=False)
                    
                    if cc_performance.empty:
                        return f"❌ No data found for Partner {partner}"
                    
                    # Find rank of current channel champ
                    current_rank = None
                    for i, cc in enumerate(cc_performance.index, 1):
                        if cc.lower() == channel_champ.lower():
                            current_rank = i
                            break
                    
                    result = f"🏁 Partner {partner} Benchmark"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"Channel Champ Ranking (by Revenue):\n"
                    
                    for i, (cc, data) in enumerate(cc_performance.head(5).iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        prefix = "👑" if i == 1 else f"{i}."
                        highlight = " ← YOU" if cc.lower() == channel_champ.lower() else ""
                        
                        result += f"{prefix} {cc}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                    
                    if current_rank and current_rank > 5:
                        result += f"\n{channel_champ} ranks #{current_rank} for {partner}"
                    
                    return result

                # Default case - show basic performance metrics
                else:
                    result = f"📊 {channel_champ}"
                    if partner:
                        result += f" × {partner}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

            except Exception as e:
                return f"❌ Error processing query: {str(e)}"




    def handle_group_channel_champ_partner_query(self, query):
            """Handle queries combining Group Channel Champ Name and Partner performance with various metrics"""
            try:
                query_lower = query.lower()
                
                # Extract Group Channel Champ Name (case-insensitive)
                group_channel_champ = None
                for name in self.df['Group Channel Champ Name'].dropna().unique():
                    if str(name).lower() in query_lower:
                        group_channel_champ = name
                        break
                
                if not group_channel_champ:
                    available_champs = self.df['Group Channel Champ Name'].dropna().unique()[:5]
                    return f"❌ Specify a Group Channel Champ. Available: {', '.join(map(str, available_champs))}"

                # Extract Partner name (case-insensitive)
                partner = None
                for partner_name in self.df['Partner'].dropna().unique():
                    if str(partner_name).lower() in query_lower:
                        partner = partner_name
                        break

                # Extract year (FY23 or 2023)
                year = None
                year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
                if year_match:
                    year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

                # Filter data
                filtered = self.df[
                    (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                ]
                if partner:
                    filtered = filtered[filtered['Partner'].str.lower() == partner.lower()]
                if year:
                    filtered = filtered[filtered['Year_Start'] == year]

                if filtered.empty:
                    return f"❌ No data for Group Channel Champ {group_channel_champ}" + \
                        (f" with Partner {partner}" if partner else "") + \
                        (f" in {year}" if year else "")

                # Calculate metrics
                total_revenue = filtered['TL Base Value'].sum()
                total_margin = filtered['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(filtered)

                # Get all Partners this group channel champ works with
                all_partners_data = self.df[
                    (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                ]
                if year:
                    all_partners_data = all_partners_data[all_partners_data['Year_Start'] == year]
                
                all_partners = all_partners_data['Partner'].unique()
                partner_count = len(all_partners)

                # Handle different query types
                
                # 1. Simple gross margin query (returns only what's asked)
                if ('gross margin' in query_lower and 'for group channel champ' in query_lower and 
                    'with partner' in query_lower and partner and not 'performance' in query_lower):
                    return f"💹 Gross Margin: {format_in_crores(total_margin)}"
                
                # 2. Gross margin performance (detailed view)
                elif ('gross margin performance' in query_lower or 
                    ('performance' in query_lower and 'gross margin' in query_lower)):
                    result = f"📊 {group_channel_champ} × {partner}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

                # 3. List top Partners by revenue
                elif ('list top' in query_lower and 'partners by revenue' in query_lower) or \
                    ('top partners by revenue' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    top_partners_list = champ_data.groupby('Partner')['TL Base Value'].sum() \
                                    .sort_values(ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Revenue for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (partner_name, revenue) in enumerate(top_partners_list.items(), 1):
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)}\n"
                    return result

                # 3a. List top Partners by gross margin
                elif ('list top' in query_lower and 'partners by gross margin' in query_lower) or \
                    ('top partners by gross margin' in query_lower) or \
                    ('list top' in query_lower and 'partners by margin' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    # Group by Partner and calculate both margin and revenue for GM%
                    partner_metrics = champ_data.groupby('Partner').agg({
                        'Gross Margin Value': 'sum',
                        'TL Base Value': 'sum'
                    })
                    partner_metrics['GM_Percent'] = (partner_metrics['Gross Margin Value'] / partner_metrics['TL Base Value'] * 100)
                    
                    # Sort by gross margin value
                    top_partners_by_margin = partner_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Gross Margin for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += ":\n"
                    
                    for i, (partner_name, data) in enumerate(top_partners_by_margin.iterrows(), 1):
                        margin = data['Gross Margin Value']
                        revenue = data['TL Base Value']
                        gm_pct = data['GM_Percent']
                        result += f"{i}. {partner_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                    return result

                # 3b. List top Partners by contribution
                elif ('list top' in query_lower and 'partners by contribution' in query_lower) or \
                    ('top partners by contribution' in query_lower) or \
                    ('list top' in query_lower and 'contribution' in query_lower):
                    # Extract number (default 5)
                    top_n = 5
                    top_match = re.search(r'top (\d+)', query_lower)
                    if top_match:
                        top_n = int(top_match.group(1))
                    
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    # Calculate total revenue for percentage calculation
                    total_champ_revenue = champ_data['TL Base Value'].sum()
                    total_champ_margin = champ_data['Gross Margin Value'].sum()
                    
                    # Group by Partner and calculate contribution metrics
                    partner_metrics = champ_data.groupby('Partner').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    
                    # Calculate contribution percentages
                    partner_metrics['Revenue_Contribution'] = (partner_metrics['TL Base Value'] / total_champ_revenue * 100)
                    partner_metrics['Margin_Contribution'] = (partner_metrics['Gross Margin Value'] / total_champ_margin * 100)
                    partner_metrics['GM_Percent'] = (partner_metrics['Gross Margin Value'] / partner_metrics['TL Base Value'] * 100)
                    
                    # Sort by revenue contribution (primary metric for "contribution")
                    top_partners_by_contribution = partner_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                    
                    result = f"🔝 Top {top_n} Partners by Contribution for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Portfolio: {format_in_crores(total_champ_revenue)} Revenue | {format_in_crores(total_champ_margin)} Margin\n\n"
                    
                    for i, (partner_name, data) in enumerate(top_partners_by_contribution.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        rev_contrib = data['Revenue_Contribution']
                        margin_contrib = data['Margin_Contribution']
                        gm_pct = data['GM_Percent']
                        
                        result += f"{i}. {partner_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                        result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                    
                    return result

                # 3c. New Partner acquisitions
                elif ('new partner acquisitions' in query_lower) or \
                    ('new partners' in query_lower and 'acquisitions' in query_lower) or \
                    ('partner acquisitions' in query_lower) or \
                    ('newly acquired partners' in query_lower):
                    
                    # Get current year or use latest available
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    previous_year = current_year - 1
                    
                    # Get Partners for current year
                    current_partners = set(self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['Partner'].unique())
                    
                    # Get Partners for previous year
                    previous_partners = set(self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                        (self.df['Year_Start'] == previous_year)
                    ]['Partner'].unique())
                    
                    # Find new Partners (in current year but not in previous year)
                    new_partners = current_partners - previous_partners
                    
                    if not new_partners:
                        return f"✅ No new Partner acquisitions for {group_channel_champ} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                    
                    # Get performance data for new Partners
                    new_partner_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year) &
                        (self.df['Partner'].isin(new_partners))
                    ]
                    
                    # Calculate metrics for new Partners
                    new_partner_metrics = new_partner_data.groupby('Partner').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    })
                    new_partner_metrics['GM_Percent'] = (new_partner_metrics['Gross Margin Value'] / new_partner_metrics['TL Base Value'] * 100)
                    new_partner_metrics['Transaction_Count'] = new_partner_data.groupby('Partner').size()
                    
                    # Sort by revenue
                    new_partner_metrics = new_partner_metrics.sort_values('TL Base Value', ascending=False)
                    
                    # Calculate totals
                    total_new_revenue = new_partner_metrics['TL Base Value'].sum()
                    total_new_margin = new_partner_metrics['Gross Margin Value'].sum()
                    total_new_transactions = new_partner_metrics['Transaction_Count'].sum()
                    avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                    
                    result = f"🆕 New Partner Acquisitions for {group_channel_champ} in FY{str(current_year)[2:]}:\n"
                    result += f"📊 Total Impact: {len(new_partners)} new Partners\n"
                    result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                    result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                    result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                    
                    result += f"🔍 Individual Performance:\n"
                    for i, (partner_name, data) in enumerate(new_partner_metrics.iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = data['GM_Percent']
                        transactions = data['Transaction_Count']
                        
                        result += f"{i}. {partner_name}:\n"
                        result += f"   • Revenue: {format_in_crores(revenue)}\n"
                        result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                        result += f"   • Transactions: {transactions:,}\n\n"
                    
                    return result

                # 4. What Partners does Group Channel Champ manage
                elif ('what partners does' in query_lower and 'manage' in query_lower) or \
                    ('partners managed' in query_lower) or ('partners handled' in query_lower):
                    
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    all_partners_with_revenue = champ_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    result = f"🤝 Partners managed by {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {len(all_partners_with_revenue)} Partners\n\n"
                    
                    if len(all_partners_with_revenue) == 0:
                        return f"❌ No Partner data found for {group_channel_champ}"
                    
                    # Show ALL Partners, not just top 5
                    result += "🔝 All Partners by Revenue:\n"
                    for i, (partner_name, revenue) in enumerate(all_partners_with_revenue.items(), 1):
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)}\n"
                    
                    return result

                # 5. Show revenue for Group Channel Champ (simple revenue query)
                elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                    result = f"💰 Revenue for {group_channel_champ}"
                    if partner:
                        result += f" with Partner {partner}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(total_revenue)}"
                    return result
                
                # 6. Gross margin across all Partners
                elif 'gross margin' in query_lower and 'across all partners' in query_lower:
                    all_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        all_data = all_data[all_data['Year_Start'] == year]
                    
                    all_margin = all_data['Gross Margin Value'].sum()
                    all_revenue = all_data['TL Base Value'].sum()
                    all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                    
                    result = f"💹 Gross Margin for {group_channel_champ} across all Partners"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                    return result
                    
                # 7. Compare YoY growth
                elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                    if not year:
                        return "❌ Please specify a year for YoY comparison"
                    
                    prev_year = year - 1
                    prev_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if partner:
                        prev_data = prev_data[prev_data['Partner'].str.lower() == partner.lower()]
                    prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                    
                    if prev_data.empty:
                        return f"❌ No data available for previous year {prev_year} to compare"
                    
                    prev_revenue = prev_data['TL Base Value'].sum()
                    prev_margin = prev_data['Gross Margin Value'].sum()
                    prev_count = len(prev_data)
                    
                    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                    margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                    count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                    
                    result = f"📈 YoY Growth for {group_channel_champ}"
                    if partner:
                        result += f" with Partner {partner}"
                    result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {count_growth:+.1f}%"
                    
                    result += f"\n\nActual Figures:\n"
                    result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                    result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                    
                    return result
                
                # 8. Highest margin Partner
                elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    partner_margins = champ_data.groupby('Partner')['Gross Margin Value'].sum() \
                                    .sort_values(ascending=False)
                    
                    if partner_margins.empty:
                        return f"❌ No margin data available for {group_channel_champ}"
                    
                    top_partner = partner_margins.index[0]
                    top_margin = partner_margins.iloc[0]
                    total_all_margin = champ_data['Gross Margin Value'].sum()
                    top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                    
                    result = f"🏆 Highest Margin Partner for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f": {top_partner}\n"
                    result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                    result += f"   • Contribution: {top_percent:.1f}% of total margin"
                    return result
                
                # 9. Partner contribution mix
                elif 'partner contribution' in query_lower or 'partner mix' in query_lower or 'contribution mix' in query_lower:
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    partner_revenues = champ_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    
                    if len(partner_revenues) == 0:
                        return f"❌ No Partner data found for {group_channel_champ}"
                    
                    total = partner_revenues.sum()
                    result = f"📊 Partner Revenue Mix for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                    
                    for i, (partner_name, revenue) in enumerate(partner_revenues.head(7).items(), 1):
                        percent = (revenue / total * 100) if total > 0 else 0
                        result += f"{i}. {partner_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                    
                    if len(partner_revenues) > 7:
                        result += f"\n+ {len(partner_revenues) - 7} more Partners"
                    
                    return result
                
                # 10. Growth potential analysis
                elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                    if not partner:
                        return "❌ Please specify a Partner for growth potential analysis"
                    
                    # Get current year data (or latest available)
                    current_year = year if year else max(self.df['Year_Start'].unique())
                    
                    # Get historical data for trend analysis (last 3 years)
                    years_to_analyze = [current_year-2, current_year-1, current_year]
                    historical_data = []
                    
                    for y in years_to_analyze:
                        year_data = self.df[
                            (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                            (self.df['Partner'].str.lower() == partner.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            revenue = year_data['TL Base Value'].sum()
                            margin = year_data['Gross Margin Value'].sum()
                            transactions = len(year_data)
                            gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                            
                            historical_data.append({
                                'year': y,
                                'revenue': revenue,
                                'margin': margin,
                                'transactions': transactions,
                                'gm_percent': gm_pct
                            })
                    
                    if len(historical_data) < 2:
                        return f"❌ Insufficient historical data for growth potential analysis"
                    
                    # Calculate trends
                    recent = historical_data[-1]
                    previous = historical_data[-2]
                    
                    revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                    margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                    transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                    
                    # Get market share within this group channel champ for this Partner
                    champ_total = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                        (self.df['Year_Start'] == current_year)
                    ]['TL Base Value'].sum()
                    
                    market_share = (recent['revenue'] / champ_total * 100) if champ_total > 0 else 0
                    
                    result = f"🚀 Growth Potential Analysis: {group_channel_champ} × {partner}\n\n"
                    result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                    result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                    result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                    result += f"   • Market Share: {market_share:.1f}% (within Champ portfolio)\n"
                    result += f"   • Transactions: {recent['transactions']:,}\n\n"
                    
                    result += f"📈 Growth Trends (YoY):\n"
                    result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                    result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                    
                    # Growth potential assessment
                    avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                    
                    if avg_growth > 20:
                        potential = "🔥 HIGH - Strong upward trajectory"
                    elif avg_growth > 10:
                        potential = "📈 MODERATE - Steady growth pattern"
                    elif avg_growth > 0:
                        potential = "🔄 LOW - Slow growth"
                    else:
                        potential = "⚠️ DECLINING - Needs attention"
                    
                    result += f"💡 Growth Potential: {potential}\n\n"
                    
                    # Historical trend
                    result += f"📅 3-Year Trend:\n"
                    for data in historical_data:
                        result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                        result += f"(GM: {data['gm_percent']:.1f}%)\n"
                    
                    return result
                
                # 11. Partner performance trend
                elif 'partner performance trend' in query_lower or 'partner trend' in query_lower or 'trend' in query_lower:
                    if not year:
                        year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                    
                    # Get data for last 3 years
                    years = [year-2, year-1, year]
                    trend_data = []
                    
                    for y in years:
                        year_data = self.df[
                            (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower()) &
                            (self.df['Year_Start'] == y)
                        ]
                        
                        if not year_data.empty:
                            partner_year = year_data.groupby('Partner')['TL Base Value'].sum().nlargest(3).to_dict()
                            total_year_revenue = year_data['TL Base Value'].sum()
                            trend_data.append({
                                'year': y,
                                'top_partners': partner_year,
                                'total_revenue': total_year_revenue
                            })
                    
                    if len(trend_data) < 2:
                        return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                    
                    result = f"📈 Partner Performance Trend for {group_channel_champ}:\n\n"
                    for entry in trend_data:
                        result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                        for i, (partner_name, revenue) in enumerate(entry['top_partners'].items(), 1):
                            result += f"   {i}. {partner_name}: {format_in_crores(revenue)}\n"
                        result += "\n"
                    
                    return result
                
                # 12. Partner dependency analysis
                elif 'partner dependency' in query_lower or 'dependency' in query_lower:
                    champ_data = self.df[
                        (self.df['Group Channel Champ Name'].str.lower() == group_channel_champ.lower())
                    ]
                    if year:
                        champ_data = champ_data[champ_data['Year_Start'] == year]
                    
                    partner_revenues = champ_data.groupby('Partner')['TL Base Value'].sum().sort_values(ascending=False)
                    total_revenue_champ = partner_revenues.sum()
                    
                    if len(partner_revenues) == 0:
                        return f"❌ No Partner data found for {group_channel_champ}"
                    
                    top_partner_share = (partner_revenues.iloc[0] / total_revenue_champ * 100) if total_revenue_champ > 0 else 0
                    top_3_share = (partner_revenues.head(3).sum() / total_revenue_champ * 100) if total_revenue_champ > 0 else 0
                    
                    result = f"⚖️ Partner Dependency Analysis for {group_channel_champ}"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"📊 Concentration Risk:\n"
                    result += f"   • Top Partner Share: {top_partner_share:.1f}%\n"
                    result += f"   • Top 3 Partners Share: {top_3_share:.1f}%\n"
                    result += f"   • Total Partners: {len(partner_revenues)}\n\n"
                    
                    # Risk assessment
                    if top_partner_share > 50:
                        risk_level = "🔴 HIGH"
                    elif top_partner_share > 30:
                        risk_level = "🟡 MEDIUM"
                    else:
                        risk_level = "🟢 LOW"
                    
                    result += f"Risk Level: {risk_level} dependency\n\n"
                    result += f"Top Partner: {partner_revenues.index[0]} ({top_partner_share:.1f}%)"
                    
                    return result
                
                # 13. Partner benchmark analysis
                elif 'partner benchmark' in query_lower or 'benchmark' in query_lower:
                    if not partner:
                        return "❌ Please specify a Partner for benchmarking"
                    
                    # Get performance of this Partner across all group channel champs
                    partner_data = self.df[self.df['Partner'].str.lower() == partner.lower()]
                    if year:
                        partner_data = partner_data[partner_data['Year_Start'] == year]
                    
                    champ_performance = partner_data.groupby('Group Channel Champ Name').agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).sort_values('TL Base Value', ascending=False)
                    
                    if champ_performance.empty:
                        return f"❌ No data found for Partner {partner}"
                    
                    # Find rank of current group channel champ
                    current_rank = None
                    for i, champ in enumerate(champ_performance.index, 1):
                        if champ.lower() == group_channel_champ.lower():
                            current_rank = i
                            break
                    
                    result = f"🏁 Partner {partner} Benchmark"
                    if year:
                        result += f" in FY{str(year)[2:]}"
                    result += f":\n\n"
                    result += f"Group Channel Champ Ranking (by Revenue):\n"
                    
                    for i, (champ, data) in enumerate(champ_performance.head(5).iterrows(), 1):
                        revenue = data['TL Base Value']
                        margin = data['Gross Margin Value']
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        prefix = "👑" if i == 1 else f"{i}."
                        highlight = " ← YOU" if champ.lower() == group_channel_champ.lower() else ""
                        
                        result += f"{prefix} {champ}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                    
                    if current_rank and current_rank > 5:
                        result += f"\n{group_channel_champ} ranks #{current_rank} for {partner}"
                    
                    return result

                # Default case - show basic performance metrics
                else:
                    result = f"📊 {group_channel_champ}"
                    if partner:
                        result += f" × {partner}"
                    if year:
                        result += f" | FY{str(year)[2:]}"
                    result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                    result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                    result += f"\n📈 Transactions: {transaction_count:,}"
                    return result

            except Exception as e:
                return f"❌ Error processing query: {str(e)}"



    def handle_business_head_oem_query(self, query):
        """Handle queries combining Business Head and OEM performance with various metrics"""
        try:
            query_lower = query.lower()
            
            # Extract Business Head name (case-insensitive)
            business_head = None
            for name in self.df['Business Head Name'].dropna().unique():
                if str(name).lower() in query_lower:
                    business_head = name
                    break
            
            if not business_head:
                available_heads = self.df['Business Head Name'].dropna().unique()[:5]
                return f"❌ Specify a Business Head. Available: {', '.join(map(str, available_heads))}"

            # Extract OEM name (case-insensitive)
            oem = None
            for oem_name in self.df['OEM'].dropna().unique():
                if str(oem_name).lower() in query_lower:
                    oem = oem_name
                    break

            # Extract year (FY23 or 2023)
            year = None
            year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
            if year_match:
                year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

            # Filter data
            filtered = self.df[
                (self.df['Business Head Name'].str.lower() == business_head.lower())
            ]
            if oem:
                filtered = filtered[filtered['OEM'].str.lower() == oem.lower()]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]

            if filtered.empty:
                return f"❌ No data for Business Head {business_head}" + \
                    (f" with OEM {oem}" if oem else "") + \
                    (f" in {year}" if year else "")

            # Calculate metrics
            total_revenue = filtered['TL Base Value'].sum()
            total_margin = filtered['Gross Margin Value'].sum()
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            transaction_count = len(filtered)

            # Get all OEMs this business head works with
            all_oems_data = self.df[
                (self.df['Business Head Name'].str.lower() == business_head.lower())
            ]
            if year:
                all_oems_data = all_oems_data[all_oems_data['Year_Start'] == year]
            
            all_oems = all_oems_data['OEM'].unique()
            oem_count = len(all_oems)

            # Handle different query types
            
            # 1. Simple gross margin query (FIXED - returns only what's asked)
            if ('gross margin' in query_lower and 'for business head' in query_lower and 
                'with oem' in query_lower and oem and not 'performance' in query_lower):
                return f"💹 Gross Margin: {format_in_crores(total_margin)}"
            
            # 2. Gross margin performance (detailed view)
            elif ('gross margin performance' in query_lower or 
                ('performance' in query_lower and 'gross margin' in query_lower)):
                result = f"📊 {business_head} × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

            # 3. List top OEMs by revenue (FIXED - shows OEMs, not total revenue)
            elif ('list top' in query_lower and 'oems by revenue' in query_lower) or \
                ('top oems by revenue' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                top_oems_list = bh_data.groupby('OEM')['TL Base Value'].sum() \
                                .sort_values(ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Revenue for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, revenue) in enumerate(top_oems_list.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                return result

            # 3a. List top OEMs by gross margin (NEW - handles margin-based ranking)
            elif ('list top' in query_lower and 'oems by gross margin' in query_lower) or \
                ('top oems by gross margin' in query_lower) or \
                ('list top' in query_lower and 'oems by margin' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                # Group by OEM and calculate both margin and revenue for GM%
                oem_metrics = bh_data.groupby('OEM').agg({
                    'Gross Margin Value': 'sum',
                    'TL Base Value': 'sum'
                })
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by gross margin value
                top_oems_by_margin = oem_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Gross Margin for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_margin.iterrows(), 1):
                    margin = data['Gross Margin Value']
                    revenue = data['TL Base Value']
                    gm_pct = data['GM_Percent']
                    result += f"{i}. {oem_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                return result

            # 3b. List top OEMs by contribution (NEW - handles contribution-based ranking)
            elif ('list top' in query_lower and 'oems by contribution' in query_lower) or \
                ('top oems by contribution' in query_lower) or \
                ('list top' in query_lower and 'contribution' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                # Calculate total revenue for percentage calculation
                total_bh_revenue = bh_data['TL Base Value'].sum()
                total_bh_margin = bh_data['Gross Margin Value'].sum()
                
                # Group by OEM and calculate contribution metrics
                oem_metrics = bh_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                
                # Calculate contribution percentages
                oem_metrics['Revenue_Contribution'] = (oem_metrics['TL Base Value'] / total_bh_revenue * 100)
                oem_metrics['Margin_Contribution'] = (oem_metrics['Gross Margin Value'] / total_bh_margin * 100)
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by revenue contribution (primary metric for "contribution")
                top_oems_by_contribution = oem_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Contribution for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Portfolio: {format_in_crores(total_bh_revenue)} Revenue | {format_in_crores(total_bh_margin)} Margin\n\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_contribution.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    rev_contrib = data['Revenue_Contribution']
                    margin_contrib = data['Margin_Contribution']
                    gm_pct = data['GM_Percent']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                    result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                
                return result

            # 3c. New OEM acquisitions (NEW - handles new OEM analysis)
            elif ('new oem acquisitions' in query_lower) or \
                ('new oems' in query_lower and 'acquisitions' in query_lower) or \
                ('oem acquisitions' in query_lower) or \
                ('newly acquired oems' in query_lower):
                
                # Get current year or use latest available
                current_year = year if year else max(self.df['Year_Start'].unique())
                previous_year = current_year - 1
                
                # Get OEMs for current year
                current_oems = set(self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['OEM'].unique())
                
                # Get OEMs for previous year
                previous_oems = set(self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                    (self.df['Year_Start'] == previous_year)
                ]['OEM'].unique())
                
                # Find new OEMs (in current year but not in previous year)
                new_oems = current_oems - previous_oems
                
                if not new_oems:
                    return f"✅ No new OEM acquisitions for {business_head} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                
                # Get performance data for new OEMs
                new_oem_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                    (self.df['Year_Start'] == current_year) &
                    (self.df['OEM'].isin(new_oems))
                ]
                
                # Calculate metrics for new OEMs
                new_oem_metrics = new_oem_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                new_oem_metrics['GM_Percent'] = (new_oem_metrics['Gross Margin Value'] / new_oem_metrics['TL Base Value'] * 100)
                new_oem_metrics['Transaction_Count'] = new_oem_data.groupby('OEM').size()
                
                # Sort by revenue
                new_oem_metrics = new_oem_metrics.sort_values('TL Base Value', ascending=False)
                
                # Calculate totals
                total_new_revenue = new_oem_metrics['TL Base Value'].sum()
                total_new_margin = new_oem_metrics['Gross Margin Value'].sum()
                total_new_transactions = new_oem_metrics['Transaction_Count'].sum()
                avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                
                result = f"🆕 New OEM Acquisitions for {business_head} in FY{str(current_year)[2:]}:\n"
                result += f"📊 Total Impact: {len(new_oems)} new OEMs\n"
                result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                
                result += f"🔍 Individual Performance:\n"
                for i, (oem_name, data) in enumerate(new_oem_metrics.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = data['GM_Percent']
                    transactions = data['Transaction_Count']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)}\n"
                    result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                    result += f"   • Transactions: {transactions:,}\n\n"
                
                return result

            # 4. What OEMs does Business Head manage (FIXED - shows all OEMs)
            elif ('what oems does' in query_lower and 'manage' in query_lower) or \
                ('oems managed' in query_lower) or ('oems handled' in query_lower):
                
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                all_oems_with_revenue = bh_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                result = f"🏭 OEMs managed by {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {len(all_oems_with_revenue)} OEMs\n\n"
                
                if len(all_oems_with_revenue) == 0:
                    return f"❌ No OEM data found for {business_head}"
                
                # Show ALL OEMs, not just top 5
                result += "🔝 All OEMs by Revenue:\n"
                for i, (oem_name, revenue) in enumerate(all_oems_with_revenue.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                
                return result

            # 5. Show revenue for Business Head (simple revenue query)
            elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                result = f"💰 Revenue for {business_head}"
                if oem:
                    result += f" with OEM {oem}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(total_revenue)}"
                return result
            
            # 6. Gross margin across all OEMs
            elif 'gross margin' in query_lower and 'across all oems' in query_lower:
                all_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    all_data = all_data[all_data['Year_Start'] == year]
                
                all_margin = all_data['Gross Margin Value'].sum()
                all_revenue = all_data['TL Base Value'].sum()
                all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                
                result = f"💹 Gross Margin for {business_head} across all OEMs"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                return result
                
            # 7. Compare YoY growth (FIXED)
            elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                if not year:
                    return "❌ Please specify a year for YoY comparison"
                
                prev_year = year - 1
                prev_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if oem:
                    prev_data = prev_data[prev_data['OEM'].str.lower() == oem.lower()]
                prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                
                if prev_data.empty:
                    return f"❌ No data available for previous year {prev_year} to compare"
                
                prev_revenue = prev_data['TL Base Value'].sum()
                prev_margin = prev_data['Gross Margin Value'].sum()
                prev_count = len(prev_data)
                
                revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                result = f"📈 YoY Growth for {business_head}"
                if oem:
                    result += f" with OEM {oem}"
                result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {count_growth:+.1f}%"
                
                result += f"\n\nActual Figures:\n"
                result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                
                return result
            
            # 8. Highest margin OEM
            elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                oem_margins = bh_data.groupby('OEM')['Gross Margin Value'].sum() \
                                .sort_values(ascending=False)
                
                if oem_margins.empty:
                    return f"❌ No margin data available for {business_head}"
                
                top_oem = oem_margins.index[0]
                top_margin = oem_margins.iloc[0]
                total_all_margin = bh_data['Gross Margin Value'].sum()
                top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                
                result = f"🏆 Highest Margin OEM for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {top_oem}\n"
                result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                result += f"   • Contribution: {top_percent:.1f}% of total margin"
                return result
            
            # 9. OEM contribution mix
            elif 'oem contribution' in query_lower or 'oem mix' in query_lower or 'contribution mix' in query_lower:
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                oem_revenues = bh_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {business_head}"
                
                total = oem_revenues.sum()
                result = f"📊 OEM Revenue Mix for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                
                for i, (oem_name, revenue) in enumerate(oem_revenues.head(7).items(), 1):
                    percent = (revenue / total * 100) if total > 0 else 0
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                
                if len(oem_revenues) > 7:
                    result += f"\n+ {len(oem_revenues) - 7} more OEMs"
                
                return result
            
            # 10. Growth potential analysis (FIXED)
            elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for growth potential analysis"
                
                # Get current year data (or latest available)
                current_year = year if year else max(self.df['Year_Start'].unique())
                
                # Get historical data for trend analysis (last 3 years)
                years_to_analyze = [current_year-2, current_year-1, current_year]
                historical_data = []
                
                for y in years_to_analyze:
                    year_data = self.df[
                        (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                        (self.df['OEM'].str.lower() == oem.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        revenue = year_data['TL Base Value'].sum()
                        margin = year_data['Gross Margin Value'].sum()
                        transactions = len(year_data)
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        historical_data.append({
                            'year': y,
                            'revenue': revenue,
                            'margin': margin,
                            'transactions': transactions,
                            'gm_percent': gm_pct
                        })
                
                if len(historical_data) < 2:
                    return f"❌ Insufficient historical data for growth potential analysis"
                
                # Calculate trends
                recent = historical_data[-1]
                previous = historical_data[-2]
                
                revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                
                # Get market share within this business head for this OEM
                bh_total = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['TL Base Value'].sum()
                
                market_share = (recent['revenue'] / bh_total * 100) if bh_total > 0 else 0
                
                result = f"🚀 Growth Potential Analysis: {business_head} × {oem}\n\n"
                result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                result += f"   • Market Share: {market_share:.1f}% (within BH portfolio)\n"
                result += f"   • Transactions: {recent['transactions']:,}\n\n"
                
                result += f"📈 Growth Trends (YoY):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                
                # Growth potential assessment
                avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                
                if avg_growth > 20:
                    potential = "🔥 HIGH - Strong upward trajectory"
                elif avg_growth > 10:
                    potential = "📈 MODERATE - Steady growth pattern"
                elif avg_growth > 0:
                    potential = "🔄 LOW - Slow growth"
                else:
                    potential = "⚠️ DECLINING - Needs attention"
                
                result += f"💡 Growth Potential: {potential}\n\n"
                
                # Historical trend
                result += f"📅 3-Year Trend:\n"
                for data in historical_data:
                    result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                    result += f"(GM: {data['gm_percent']:.1f}%)\n"
                
                return result
            
            # 11. OEM performance trend
            elif 'oem performance trend' in query_lower or 'oem trend' in query_lower or 'trend' in query_lower:
                if not year:
                    year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                
                # Get data for last 3 years
                years = [year-2, year-1, year]
                trend_data = []
                
                for y in years:
                    year_data = self.df[
                        (self.df['Business Head Name'].str.lower() == business_head.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        oem_year = year_data.groupby('OEM')['TL Base Value'].sum().nlargest(3).to_dict()
                        total_year_revenue = year_data['TL Base Value'].sum()
                        trend_data.append({
                            'year': y,
                            'top_oems': oem_year,
                            'total_revenue': total_year_revenue
                        })
                
                if len(trend_data) < 2:
                    return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                
                result = f"📈 OEM Performance Trend for {business_head}:\n\n"
                for entry in trend_data:
                    result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                    for i, (oem_name, revenue) in enumerate(entry['top_oems'].items(), 1):
                        result += f"   {i}. {oem_name}: {format_in_crores(revenue)}\n"
                    result += "\n"
                
                return result
            
            # 12. OEM dependency analysis
            elif 'oem dependency' in query_lower or 'dependency' in query_lower:
                bh_data = self.df[
                    (self.df['Business Head Name'].str.lower() == business_head.lower())
                ]
                if year:
                    bh_data = bh_data[bh_data['Year_Start'] == year]
                
                oem_revenues = bh_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                total_revenue_bh = oem_revenues.sum()
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {business_head}"
                
                top_oem_share = (oem_revenues.iloc[0] / total_revenue_bh * 100) if total_revenue_bh > 0 else 0
                top_3_share = (oem_revenues.head(3).sum() / total_revenue_bh * 100) if total_revenue_bh > 0 else 0
                
                result = f"⚖️ OEM Dependency Analysis for {business_head}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"📊 Concentration Risk:\n"
                result += f"   • Top OEM Share: {top_oem_share:.1f}%\n"
                result += f"   • Top 3 OEMs Share: {top_3_share:.1f}%\n"
                result += f"   • Total OEMs: {len(oem_revenues)}\n\n"
                
                # Risk assessment
                if top_oem_share > 50:
                    risk_level = "🔴 HIGH"
                elif top_oem_share > 30:
                    risk_level = "🟡 MEDIUM"
                else:
                    risk_level = "🟢 LOW"
                
                result += f"Risk Level: {risk_level} dependency\n\n"
                result += f"Top OEM: {oem_revenues.index[0]} ({top_oem_share:.1f}%)"
                
                return result
            
            # 13. OEM benchmark analysis
            elif 'oem benchmark' in query_lower or 'benchmark' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for benchmarking"
                
                # Get performance of this OEM across all business heads
                oem_data = self.df[self.df['OEM'].str.lower() == oem.lower()]
                if year:
                    oem_data = oem_data[oem_data['Year_Start'] == year]
                
                bh_performance = oem_data.groupby('Business Head Name').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_values('TL Base Value', ascending=False)
                
                if bh_performance.empty:
                    return f"❌ No data found for OEM {oem}"
                
                # Find rank of current business head
                current_rank = None
                for i, bh in enumerate(bh_performance.index, 1):
                    if bh.lower() == business_head.lower():
                        current_rank = i
                        break
                
                result = f"🏁 OEM {oem} Benchmark"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"Business Head Ranking (by Revenue):\n"
                
                for i, (bh, data) in enumerate(bh_performance.head(5).iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                    
                    prefix = "👑" if i == 1 else f"{i}."
                    highlight = " ← YOU" if bh.lower() == business_head.lower() else ""
                    
                    result += f"{prefix} {bh}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                
                if current_rank and current_rank > 5:
                    result += f"\n{business_head} ranks #{current_rank} for {oem}"
                
                return result

            # Default case - show basic performance metrics
            else:
                result = f"📊 {business_head}"
                if oem:
                    result += f" × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"


    def handle_group_business_manager_oem_query(self, query):
        """Handle queries combining Group Business Manager and OEM performance with various metrics"""
        try:
            query_lower = query.lower()
            
            # Extract Group Business Manager name (case-insensitive)
            group_business_manager = None
            for name in self.df['Group Business Manager Name'].dropna().unique():
                if str(name).lower() in query_lower:
                    group_business_manager = name
                    break
            
            if not group_business_manager:
                available_managers = self.df['Group Business Manager Name'].dropna().unique()[:5]
                return f"❌ Specify a Group Business Manager. Available: {', '.join(map(str, available_managers))}"

            # Extract OEM name (case-insensitive)
            oem = None
            for oem_name in self.df['OEM'].dropna().unique():
                if str(oem_name).lower() in query_lower:
                    oem = oem_name
                    break

            # Extract year (FY23 or 2023)
            year = None
            year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
            if year_match:
                year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

            # Filter data
            filtered = self.df[
                (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
            ]
            if oem:
                filtered = filtered[filtered['OEM'].str.lower() == oem.lower()]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]

            if filtered.empty:
                return f"❌ No data for Group Business Manager {group_business_manager}" + \
                    (f" with OEM {oem}" if oem else "") + \
                    (f" in {year}" if year else "")

            # Calculate metrics
            total_revenue = filtered['TL Base Value'].sum()
            total_margin = filtered['Gross Margin Value'].sum()
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            transaction_count = len(filtered)

            # Get all OEMs this group business manager works with
            all_oems_data = self.df[
                (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
            ]
            if year:
                all_oems_data = all_oems_data[all_oems_data['Year_Start'] == year]
            
            all_oems = all_oems_data['OEM'].unique()
            oem_count = len(all_oems)

            # Handle different query types
            
            # 1. Simple gross margin query (FIXED - returns only what's asked)
            if ('gross margin' in query_lower and 'for group business manager' in query_lower and 
                'with oem' in query_lower and oem and not 'performance' in query_lower):
                return f"💹 Gross Margin: {format_in_crores(total_margin)}"
            
            # 2. Gross margin performance (detailed view)
            elif ('gross margin performance' in query_lower or 
                ('performance' in query_lower and 'gross margin' in query_lower)):
                result = f"📊 {group_business_manager} × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

            # 3. List top OEMs by revenue (FIXED - shows OEMs, not total revenue)
            elif ('list top' in query_lower and 'oems by revenue' in query_lower) or \
                ('top oems by revenue' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                top_oems_list = gbm_data.groupby('OEM')['TL Base Value'].sum() \
                                .sort_values(ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Revenue for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, revenue) in enumerate(top_oems_list.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                return result

            # 3a. List top OEMs by gross margin (NEW - handles margin-based ranking)
            elif ('list top' in query_lower and 'oems by gross margin' in query_lower) or \
                ('top oems by gross margin' in query_lower) or \
                ('list top' in query_lower and 'oems by margin' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                # Group by OEM and calculate both margin and revenue for GM%
                oem_metrics = gbm_data.groupby('OEM').agg({
                    'Gross Margin Value': 'sum',
                    'TL Base Value': 'sum'
                })
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by gross margin value
                top_oems_by_margin = oem_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Gross Margin for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_margin.iterrows(), 1):
                    margin = data['Gross Margin Value']
                    revenue = data['TL Base Value']
                    gm_pct = data['GM_Percent']
                    result += f"{i}. {oem_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                return result

            # 3b. List top OEMs by contribution (NEW - handles contribution-based ranking)
            elif ('list top' in query_lower and 'oems by contribution' in query_lower) or \
                ('top oems by contribution' in query_lower) or \
                ('list top' in query_lower and 'contribution' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                # Calculate total revenue for percentage calculation
                total_gbm_revenue = gbm_data['TL Base Value'].sum()
                total_gbm_margin = gbm_data['Gross Margin Value'].sum()
                
                # Group by OEM and calculate contribution metrics
                oem_metrics = gbm_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                
                # Calculate contribution percentages
                oem_metrics['Revenue_Contribution'] = (oem_metrics['TL Base Value'] / total_gbm_revenue * 100)
                oem_metrics['Margin_Contribution'] = (oem_metrics['Gross Margin Value'] / total_gbm_margin * 100)
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by revenue contribution (primary metric for "contribution")
                top_oems_by_contribution = oem_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Contribution for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Portfolio: {format_in_crores(total_gbm_revenue)} Revenue | {format_in_crores(total_gbm_margin)} Margin\n\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_contribution.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    rev_contrib = data['Revenue_Contribution']
                    margin_contrib = data['Margin_Contribution']
                    gm_pct = data['GM_Percent']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                    result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                
                return result

            # 3c. New OEM acquisitions (NEW - handles new OEM analysis)
            elif ('new oem acquisitions' in query_lower) or \
                ('new oems' in query_lower and 'acquisitions' in query_lower) or \
                ('oem acquisitions' in query_lower) or \
                ('newly acquired oems' in query_lower):
                
                # Get current year or use latest available
                current_year = year if year else max(self.df['Year_Start'].unique())
                previous_year = current_year - 1
                
                # Get OEMs for current year
                current_oems = set(self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['OEM'].unique())
                
                # Get OEMs for previous year
                previous_oems = set(self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                    (self.df['Year_Start'] == previous_year)
                ]['OEM'].unique())
                
                # Find new OEMs (in current year but not in previous year)
                new_oems = current_oems - previous_oems
                
                if not new_oems:
                    return f"✅ No new OEM acquisitions for {group_business_manager} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                
                # Get performance data for new OEMs
                new_oem_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                    (self.df['Year_Start'] == current_year) &
                    (self.df['OEM'].isin(new_oems))
                ]
                
                # Calculate metrics for new OEMs
                new_oem_metrics = new_oem_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                new_oem_metrics['GM_Percent'] = (new_oem_metrics['Gross Margin Value'] / new_oem_metrics['TL Base Value'] * 100)
                new_oem_metrics['Transaction_Count'] = new_oem_data.groupby('OEM').size()
                
                # Sort by revenue
                new_oem_metrics = new_oem_metrics.sort_values('TL Base Value', ascending=False)
                
                # Calculate totals
                total_new_revenue = new_oem_metrics['TL Base Value'].sum()
                total_new_margin = new_oem_metrics['Gross Margin Value'].sum()
                total_new_transactions = new_oem_metrics['Transaction_Count'].sum()
                avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                
                result = f"🆕 New OEM Acquisitions for {group_business_manager} in FY{str(current_year)[2:]}:\n"
                result += f"📊 Total Impact: {len(new_oems)} new OEMs\n"
                result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                
                result += f"🔍 Individual Performance:\n"
                for i, (oem_name, data) in enumerate(new_oem_metrics.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = data['GM_Percent']
                    transactions = data['Transaction_Count']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)}\n"
                    result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                    result += f"   • Transactions: {transactions:,}\n\n"
                
                return result

            # 4. What OEMs does Group Business Manager manage (FIXED - shows all OEMs)
            elif ('what oems does' in query_lower and 'manage' in query_lower) or \
                ('oems managed' in query_lower) or ('oems handled' in query_lower):
                
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                all_oems_with_revenue = gbm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                result = f"🏭 OEMs managed by {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {len(all_oems_with_revenue)} OEMs\n\n"
                
                if len(all_oems_with_revenue) == 0:
                    return f"❌ No OEM data found for {group_business_manager}"
                
                # Show ALL OEMs, not just top 5
                result += "🔝 All OEMs by Revenue:\n"
                for i, (oem_name, revenue) in enumerate(all_oems_with_revenue.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                
                return result

            # 5. Show revenue for Group Business Manager (simple revenue query)
            elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                result = f"💰 Revenue for {group_business_manager}"
                if oem:
                    result += f" with OEM {oem}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(total_revenue)}"
                return result
            
            # 6. Gross margin across all OEMs
            elif 'gross margin' in query_lower and 'across all oems' in query_lower:
                all_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    all_data = all_data[all_data['Year_Start'] == year]
                
                all_margin = all_data['Gross Margin Value'].sum()
                all_revenue = all_data['TL Base Value'].sum()
                all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                
                result = f"💹 Gross Margin for {group_business_manager} across all OEMs"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                return result
                
            # 7. Compare YoY growth (FIXED)
            elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                if not year:
                    return "❌ Please specify a year for YoY comparison"
                
                prev_year = year - 1
                prev_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if oem:
                    prev_data = prev_data[prev_data['OEM'].str.lower() == oem.lower()]
                prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                
                if prev_data.empty:
                    return f"❌ No data available for previous year {prev_year} to compare"
                
                prev_revenue = prev_data['TL Base Value'].sum()
                prev_margin = prev_data['Gross Margin Value'].sum()
                prev_count = len(prev_data)
                
                revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                result = f"📈 YoY Growth for {group_business_manager}"
                if oem:
                    result += f" with OEM {oem}"
                result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {count_growth:+.1f}%"
                
                result += f"\n\nActual Figures:\n"
                result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                
                return result
            
            # 8. Highest margin OEM
            elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                oem_margins = gbm_data.groupby('OEM')['Gross Margin Value'].sum() \
                                .sort_values(ascending=False)
                
                if oem_margins.empty:
                    return f"❌ No margin data available for {group_business_manager}"
                
                top_oem = oem_margins.index[0]
                top_margin = oem_margins.iloc[0]
                total_all_margin = gbm_data['Gross Margin Value'].sum()
                top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                
                result = f"🏆 Highest Margin OEM for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {top_oem}\n"
                result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                result += f"   • Contribution: {top_percent:.1f}% of total margin"
                return result
            
            # 9. OEM contribution mix
            elif 'oem contribution' in query_lower or 'oem mix' in query_lower or 'contribution mix' in query_lower:
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                oem_revenues = gbm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {group_business_manager}"
                
                total = oem_revenues.sum()
                result = f"📊 OEM Revenue Mix for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                
                for i, (oem_name, revenue) in enumerate(oem_revenues.head(7).items(), 1):
                    percent = (revenue / total * 100) if total > 0 else 0
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                
                if len(oem_revenues) > 7:
                    result += f"\n+ {len(oem_revenues) - 7} more OEMs"
                
                return result
            
            # 10. Growth potential analysis (FIXED)
            elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for growth potential analysis"
                
                # Get current year data (or latest available)
                current_year = year if year else max(self.df['Year_Start'].unique())
                
                # Get historical data for trend analysis (last 3 years)
                years_to_analyze = [current_year-2, current_year-1, current_year]
                historical_data = []
                
                for y in years_to_analyze:
                    year_data = self.df[
                        (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                        (self.df['OEM'].str.lower() == oem.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        revenue = year_data['TL Base Value'].sum()
                        margin = year_data['Gross Margin Value'].sum()
                        transactions = len(year_data)
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        historical_data.append({
                            'year': y,
                            'revenue': revenue,
                            'margin': margin,
                            'transactions': transactions,
                            'gm_percent': gm_pct
                        })
                
                if len(historical_data) < 2:
                    return f"❌ Insufficient historical data for growth potential analysis"
                
                # Calculate trends
                recent = historical_data[-1]
                previous = historical_data[-2]
                
                revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                
                # Get market share within this group business manager for this OEM
                gbm_total = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['TL Base Value'].sum()
                
                market_share = (recent['revenue'] / gbm_total * 100) if gbm_total > 0 else 0
                
                result = f"🚀 Growth Potential Analysis: {group_business_manager} × {oem}\n\n"
                result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                result += f"   • Market Share: {market_share:.1f}% (within GBM portfolio)\n"
                result += f"   • Transactions: {recent['transactions']:,}\n\n"
                
                result += f"📈 Growth Trends (YoY):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                
                # Growth potential assessment
                avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                
                if avg_growth > 20:
                    potential = "🔥 HIGH - Strong upward trajectory"
                elif avg_growth > 10:
                    potential = "📈 MODERATE - Steady growth pattern"
                elif avg_growth > 0:
                    potential = "🔄 LOW - Slow growth"
                else:
                    potential = "⚠️ DECLINING - Needs attention"
                
                result += f"💡 Growth Potential: {potential}\n\n"
                
                # Historical trend
                result += f"📅 3-Year Trend:\n"
                for data in historical_data:
                    result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                    result += f"(GM: {data['gm_percent']:.1f}%)\n"
                
                return result
            
            # 11. OEM performance trend
            elif 'oem performance trend' in query_lower or 'oem trend' in query_lower or 'trend' in query_lower:
                if not year:
                    year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                
                # Get data for last 3 years
                years = [year-2, year-1, year]
                trend_data = []
                
                for y in years:
                    year_data = self.df[
                        (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        oem_year = year_data.groupby('OEM')['TL Base Value'].sum().nlargest(3).to_dict()
                        total_year_revenue = year_data['TL Base Value'].sum()
                        trend_data.append({
                            'year': y,
                            'top_oems': oem_year,
                            'total_revenue': total_year_revenue
                        })
                
                if len(trend_data) < 2:
                    return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                
                result = f"📈 OEM Performance Trend for {group_business_manager}:\n\n"
                for entry in trend_data:
                    result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                    for i, (oem_name, revenue) in enumerate(entry['top_oems'].items(), 1):
                        result += f"   {i}. {oem_name}: {format_in_crores(revenue)}\n"
                    result += "\n"
                
                return result
            
            # 12. OEM dependency analysis
            elif 'oem dependency' in query_lower or 'dependency' in query_lower:
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                
                oem_revenues = gbm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                total_revenue_gbm = oem_revenues.sum()
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {group_business_manager}"
                
                top_oem_share = (oem_revenues.iloc[0] / total_revenue_gbm * 100) if total_revenue_gbm > 0 else 0
                top_3_share = (oem_revenues.head(3).sum() / total_revenue_gbm * 100) if total_revenue_gbm > 0 else 0
                
                result = f"⚖️ OEM Dependency Analysis for {group_business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"📊 Concentration Risk:\n"
                result += f"   • Top OEM Share: {top_oem_share:.1f}%\n"
                result += f"   • Top 3 OEMs Share: {top_3_share:.1f}%\n"
                result += f"   • Total OEMs: {len(oem_revenues)}\n\n"
                
                # Risk assessment
                if top_oem_share > 50:
                    risk_level = "🔴 HIGH"
                elif top_oem_share > 30:
                    risk_level = "🟡 MEDIUM"
                else:
                    risk_level = "🟢 LOW"
                
                result += f"Risk Level: {risk_level} dependency\n\n"
                result += f"Top OEM: {oem_revenues.index[0]} ({top_oem_share:.1f}%)"
                
                return result
            
            # 13. OEM benchmark analysis
            elif 'oem benchmark' in query_lower or 'benchmark' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for benchmarking"
                
                # Get performance of this OEM across all group business managers
                oem_data = self.df[self.df['OEM'].str.lower() == oem.lower()]
                if year:
                    oem_data = oem_data[oem_data['Year_Start'] == year]
                
                gbm_performance = oem_data.groupby('Group Business Manager Name').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_values('TL Base Value', ascending=False)
                
                if gbm_performance.empty:
                    return f"❌ No data found for OEM {oem}"
                
                # Find rank of current group business manager
                current_rank = None
                for i, gbm in enumerate(gbm_performance.index, 1):
                    if gbm.lower() == group_business_manager.lower():
                        current_rank = i
                        break
                
                result = f"🏁 OEM {oem} Benchmark"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"Group Business Manager Ranking (by Revenue):\n"
                
                for i, (gbm, data) in enumerate(gbm_performance.head(5).iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                    
                    prefix = "👑" if i == 1 else f"{i}."
                    highlight = " ← YOU" if gbm.lower() == group_business_manager.lower() else ""
                    
                    result += f"{prefix} {gbm}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                
                if current_rank and current_rank > 5:
                    result += f"\n{group_business_manager} ranks #{current_rank} for {oem}"
                
                return result

            # 14. Team performance analysis (NEW - shows Business Heads under this GBM)
            elif 'team performance' in query_lower or 'team analysis' in query_lower or 'business heads under' in query_lower:
                # Analyze team performance under this Group Business Manager
                gbm_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == group_business_manager.lower())
                ]
                if year:
                    gbm_data = gbm_data[gbm_data['Year_Start'] == year]
                if oem:
                    gbm_data = gbm_data[gbm_data['OEM'].str.lower() == oem.lower()]
                
                # Get Business Heads under this GBM
                business_heads = gbm_data.groupby('Business Head Name').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_values('TL Base Value', ascending=False)
                
                if business_heads.empty:
                    return f"❌ No Business Head data found under {group_business_manager}"
                
                result = f"👥 Team Performance for {group_business_manager}"
                if oem:
                    result += f" with OEM {oem}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                
                result += f"Business Heads Managed: {len(business_heads)}\n\n"
                result += "🔝 Top Business Heads by Revenue:\n"
                
                for i, (bh_name, data) in enumerate(business_heads.head(5).iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                    result += f"{i}. {bh_name}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%)\n"
                
                if len(business_heads) > 5:
                    result += f"\n+ {len(business_heads) - 5} more Business Heads"
                
                return result

            # Default case - show basic performance metrics
            else:
                result = f"📊 {group_business_manager}"
                if oem:
                    result += f" × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    

    def handle_business_manager_oem_query(self, query):
        """Handle queries combining Business Manager and OEM performance with various metrics"""
        try:
            query_lower = query.lower()
            
            # Extract Business Manager name (case-insensitive)
            business_manager = None
            for name in self.df['Business Manager Name'].dropna().unique():
                if str(name).lower() in query_lower:
                    business_manager = name
                    break
            
            if not business_manager:
                available_managers = self.df['Business Manager Name'].dropna().unique()[:5]
                return f"❌ Specify a Business Manager. Available: {', '.join(map(str, available_managers))}"

            # Extract OEM name (case-insensitive)
            oem = None
            for oem_name in self.df['OEM'].dropna().unique():
                if str(oem_name).lower() in query_lower:
                    oem = oem_name
                    break

            # Extract year (FY23 or 2023)
            year = None
            year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
            if year_match:
                year = 2000 + int(year_match.group(2))  # Handles FY23 or 2023

            # Filter data
            filtered = self.df[
                (self.df['Business Manager Name'].str.lower() == business_manager.lower())
            ]
            if oem:
                filtered = filtered[filtered['OEM'].str.lower() == oem.lower()]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]

            if filtered.empty:
                return f"❌ No data for Business Manager {business_manager}" + \
                    (f" with OEM {oem}" if oem else "") + \
                    (f" in {year}" if year else "")

            # Calculate metrics
            total_revenue = filtered['TL Base Value'].sum()
            total_margin = filtered['Gross Margin Value'].sum()
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            transaction_count = len(filtered)

            # Get all OEMs this business manager works with
            all_oems_data = self.df[
                (self.df['Business Manager Name'].str.lower() == business_manager.lower())
            ]
            if year:
                all_oems_data = all_oems_data[all_oems_data['Year_Start'] == year]
            
            all_oems = all_oems_data['OEM'].unique()
            oem_count = len(all_oems)

            # Handle different query types
            
            # 1. Simple gross margin query
            if ('gross margin' in query_lower and 'for business manager' in query_lower and 
                'with oem' in query_lower and oem and not 'performance' in query_lower):
                return f"💹 Gross Margin: {format_in_crores(total_margin)}"
            
            # 2. Gross margin performance (detailed view)
            elif ('gross margin performance' in query_lower or 
                ('performance' in query_lower and 'gross margin' in query_lower)):
                result = f"📊 {business_manager} × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

            # 3. List top OEMs by revenue
            elif ('list top' in query_lower and 'oems by revenue' in query_lower) or \
                ('top oems by revenue' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                top_oems_list = bm_data.groupby('OEM')['TL Base Value'].sum() \
                                .sort_values(ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Revenue for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, revenue) in enumerate(top_oems_list.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                return result

            # 3a. List top OEMs by gross margin
            elif ('list top' in query_lower and 'oems by gross margin' in query_lower) or \
                ('top oems by gross margin' in query_lower) or \
                ('list top' in query_lower and 'oems by margin' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                # Group by OEM and calculate both margin and revenue for GM%
                oem_metrics = bm_data.groupby('OEM').agg({
                    'Gross Margin Value': 'sum',
                    'TL Base Value': 'sum'
                })
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by gross margin value
                top_oems_by_margin = oem_metrics.sort_values('Gross Margin Value', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Gross Margin for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += ":\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_margin.iterrows(), 1):
                    margin = data['Gross Margin Value']
                    revenue = data['TL Base Value']
                    gm_pct = data['GM_Percent']
                    result += f"{i}. {oem_name}: {format_in_crores(margin)} (GM%: {gm_pct:.1f}% | Revenue: {format_in_crores(revenue)})\n"
                return result

            # 3b. List top OEMs by contribution
            elif ('list top' in query_lower and 'oems by contribution' in query_lower) or \
                ('top oems by contribution' in query_lower) or \
                ('list top' in query_lower and 'contribution' in query_lower):
                # Extract number (default 5)
                top_n = 5
                top_match = re.search(r'top (\d+)', query_lower)
                if top_match:
                    top_n = int(top_match.group(1))
                
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                # Calculate total revenue for percentage calculation
                total_bm_revenue = bm_data['TL Base Value'].sum()
                total_bm_margin = bm_data['Gross Margin Value'].sum()
                
                # Group by OEM and calculate contribution metrics
                oem_metrics = bm_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                
                # Calculate contribution percentages
                oem_metrics['Revenue_Contribution'] = (oem_metrics['TL Base Value'] / total_bm_revenue * 100)
                oem_metrics['Margin_Contribution'] = (oem_metrics['Gross Margin Value'] / total_bm_margin * 100)
                oem_metrics['GM_Percent'] = (oem_metrics['Gross Margin Value'] / oem_metrics['TL Base Value'] * 100)
                
                # Sort by revenue contribution (primary metric for "contribution")
                top_oems_by_contribution = oem_metrics.sort_values('Revenue_Contribution', ascending=False).head(top_n)
                
                result = f"🔝 Top {top_n} OEMs by Contribution for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Portfolio: {format_in_crores(total_bm_revenue)} Revenue | {format_in_crores(total_bm_margin)} Margin\n\n"
                
                for i, (oem_name, data) in enumerate(top_oems_by_contribution.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    rev_contrib = data['Revenue_Contribution']
                    margin_contrib = data['Margin_Contribution']
                    gm_pct = data['GM_Percent']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)} ({rev_contrib:.1f}% contribution)\n"
                    result += f"   • Margin: {format_in_crores(margin)} ({margin_contrib:.1f}% contribution | GM%: {gm_pct:.1f}%)\n\n"
                
                return result

            # 3c. New OEM acquisitions
            elif ('new oem acquisitions' in query_lower) or \
                ('new oems' in query_lower and 'acquisitions' in query_lower) or \
                ('oem acquisitions' in query_lower) or \
                ('newly acquired oems' in query_lower):
                
                # Get current year or use latest available
                current_year = year if year else max(self.df['Year_Start'].unique())
                previous_year = current_year - 1
                
                # Get OEMs for current year
                current_oems = set(self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['OEM'].unique())
                
                # Get OEMs for previous year
                previous_oems = set(self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                    (self.df['Year_Start'] == previous_year)
                ]['OEM'].unique())
                
                # Find new OEMs (in current year but not in previous year)
                new_oems = current_oems - previous_oems
                
                if not new_oems:
                    return f"✅ No new OEM acquisitions for {business_manager} in FY{str(current_year)[2:]} (compared to FY{str(previous_year)[2:]})"
                
                # Get performance data for new OEMs
                new_oem_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                    (self.df['Year_Start'] == current_year) &
                    (self.df['OEM'].isin(new_oems))
                ]
                
                # Calculate metrics for new OEMs
                new_oem_metrics = new_oem_data.groupby('OEM').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                })
                new_oem_metrics['GM_Percent'] = (new_oem_metrics['Gross Margin Value'] / new_oem_metrics['TL Base Value'] * 100)
                new_oem_metrics['Transaction_Count'] = new_oem_data.groupby('OEM').size()
                
                # Sort by revenue
                new_oem_metrics = new_oem_metrics.sort_values('TL Base Value', ascending=False)
                
                # Calculate totals
                total_new_revenue = new_oem_metrics['TL Base Value'].sum()
                total_new_margin = new_oem_metrics['Gross Margin Value'].sum()
                total_new_transactions = new_oem_metrics['Transaction_Count'].sum()
                avg_gm_percent = (total_new_margin / total_new_revenue * 100) if total_new_revenue > 0 else 0
                
                result = f"🆕 New OEM Acquisitions for {business_manager} in FY{str(current_year)[2:]}:\n"
                result += f"📊 Total Impact: {len(new_oems)} new OEMs\n"
                result += f"💰 Combined Revenue: {format_in_crores(total_new_revenue)}\n"
                result += f"💹 Combined Margin: {format_in_crores(total_new_margin)} (GM%: {avg_gm_percent:.1f}%)\n"
                result += f"📈 Total Transactions: {total_new_transactions:,}\n\n"
                
                result += f"🔍 Individual Performance:\n"
                for i, (oem_name, data) in enumerate(new_oem_metrics.iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = data['GM_Percent']
                    transactions = data['Transaction_Count']
                    
                    result += f"{i}. {oem_name}:\n"
                    result += f"   • Revenue: {format_in_crores(revenue)}\n"
                    result += f"   • Margin: {format_in_crores(margin)} (GM%: {gm_pct:.1f}%)\n"
                    result += f"   • Transactions: {transactions:,}\n\n"
                
                return result

            # 4. What OEMs does Business Manager manage
            elif ('what oems does' in query_lower and 'manage' in query_lower) or \
                ('oems managed' in query_lower) or ('oems handled' in query_lower):
                
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                all_oems_with_revenue = bm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                result = f"🏭 OEMs managed by {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {len(all_oems_with_revenue)} OEMs\n\n"
                
                if len(all_oems_with_revenue) == 0:
                    return f"❌ No OEM data found for {business_manager}"
                
                # Show ALL OEMs, not just top 5
                result += "🔝 All OEMs by Revenue:\n"
                for i, (oem_name, revenue) in enumerate(all_oems_with_revenue.items(), 1):
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)}\n"
                
                return result

            # 5. Show revenue for Business Manager (simple revenue query)
            elif 'show revenue' in query_lower or ('revenue for' in query_lower and not 'top' in query_lower):
                result = f"💰 Revenue for {business_manager}"
                if oem:
                    result += f" with OEM {oem}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(total_revenue)}"
                return result
            
            # 6. Gross margin across all OEMs
            elif 'gross margin' in query_lower and 'across all oems' in query_lower:
                all_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    all_data = all_data[all_data['Year_Start'] == year]
                
                all_margin = all_data['Gross Margin Value'].sum()
                all_revenue = all_data['TL Base Value'].sum()
                all_gm_percent = (all_margin / all_revenue * 100) if all_revenue > 0 else 0
                
                result = f"💹 Gross Margin for {business_manager} across all OEMs"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {format_in_crores(all_margin)} (GM%: {all_gm_percent:.1f}%)"
                return result
                
            # 7. Compare YoY growth
            elif 'compare yoy growth' in query_lower or 'year over year' in query_lower or 'yoy' in query_lower:
                if not year:
                    return "❌ Please specify a year for YoY comparison"
                
                prev_year = year - 1
                prev_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if oem:
                    prev_data = prev_data[prev_data['OEM'].str.lower() == oem.lower()]
                prev_data = prev_data[prev_data['Year_Start'] == prev_year]
                
                if prev_data.empty:
                    return f"❌ No data available for previous year {prev_year} to compare"
                
                prev_revenue = prev_data['TL Base Value'].sum()
                prev_margin = prev_data['Gross Margin Value'].sum()
                prev_count = len(prev_data)
                
                revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                result = f"📈 YoY Growth for {business_manager}"
                if oem:
                    result += f" with OEM {oem}"
                result += f" (FY{str(prev_year)[2:]} → FY{str(year)[2:]}):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {count_growth:+.1f}%"
                
                result += f"\n\nActual Figures:\n"
                result += f"   • Revenue: {format_in_crores(prev_revenue)} → {format_in_crores(total_revenue)}\n"
                result += f"   • Gross Margin: {format_in_crores(prev_margin)} → {format_in_crores(total_margin)}"
                
                return result
            
            # 8. Highest margin OEM
            elif 'highest margin' in query_lower or 'contributes the highest margin' in query_lower or 'best margin' in query_lower:
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                oem_margins = bm_data.groupby('OEM')['Gross Margin Value'].sum() \
                                .sort_values(ascending=False)
                
                if oem_margins.empty:
                    return f"❌ No margin data available for {business_manager}"
                
                top_oem = oem_margins.index[0]
                top_margin = oem_margins.iloc[0]
                total_all_margin = bm_data['Gross Margin Value'].sum()
                top_percent = (top_margin / total_all_margin * 100) if total_all_margin > 0 else 0
                
                result = f"🏆 Highest Margin OEM for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f": {top_oem}\n"
                result += f"   • Gross Margin: {format_in_crores(top_margin)}\n"
                result += f"   • Contribution: {top_percent:.1f}% of total margin"
                return result
            
            # 9. OEM contribution mix
            elif 'oem contribution' in query_lower or 'oem mix' in query_lower or 'contribution mix' in query_lower:
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                oem_revenues = bm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {business_manager}"
                
                total = oem_revenues.sum()
                result = f"📊 OEM Revenue Mix for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f"\nTotal Revenue: {format_in_crores(total)}\n\n"
                
                for i, (oem_name, revenue) in enumerate(oem_revenues.head(7).items(), 1):
                    percent = (revenue / total * 100) if total > 0 else 0
                    result += f"{i}. {oem_name}: {format_in_crores(revenue)} ({percent:.1f}%)\n"
                
                if len(oem_revenues) > 7:
                    result += f"\n+ {len(oem_revenues) - 7} more OEMs"
                
                return result
            
            # 10. Growth potential analysis
            elif 'growth potential' in query_lower or 'potential analysis' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for growth potential analysis"
                
                # Get current year data (or latest available)
                current_year = year if year else max(self.df['Year_Start'].unique())
                
                # Get historical data for trend analysis (last 3 years)
                years_to_analyze = [current_year-2, current_year-1, current_year]
                historical_data = []
                
                for y in years_to_analyze:
                    year_data = self.df[
                        (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                        (self.df['OEM'].str.lower() == oem.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        revenue = year_data['TL Base Value'].sum()
                        margin = year_data['Gross Margin Value'].sum()
                        transactions = len(year_data)
                        gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                        
                        historical_data.append({
                            'year': y,
                            'revenue': revenue,
                            'margin': margin,
                            'transactions': transactions,
                            'gm_percent': gm_pct
                        })
                
                if len(historical_data) < 2:
                    return f"❌ Insufficient historical data for growth potential analysis"
                
                # Calculate trends
                recent = historical_data[-1]
                previous = historical_data[-2]
                
                revenue_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] > 0 else 0
                margin_growth = ((recent['margin'] - previous['margin']) / previous['margin'] * 100) if previous['margin'] > 0 else 0
                transaction_growth = ((recent['transactions'] - previous['transactions']) / previous['transactions'] * 100) if previous['transactions'] > 0 else 0
                
                # Get market share within this business manager for this OEM
                bm_total = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                    (self.df['Year_Start'] == current_year)
                ]['TL Base Value'].sum()
                
                market_share = (recent['revenue'] / bm_total * 100) if bm_total > 0 else 0
                
                result = f"🚀 Growth Potential Analysis: {business_manager} × {oem}\n\n"
                result += f"📊 Current Performance (FY{str(current_year)[2:]}):\n"
                result += f"   • Revenue: {format_in_crores(recent['revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(recent['margin'])} ({recent['gm_percent']:.1f}%)\n"
                result += f"   • Market Share: {market_share:.1f}% (within BM portfolio)\n"
                result += f"   • Transactions: {recent['transactions']:,}\n\n"
                
                result += f"📈 Growth Trends (YoY):\n"
                result += f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                result += f"   • Margin Growth: {margin_growth:+.1f}%\n"
                result += f"   • Transaction Growth: {transaction_growth:+.1f}%\n\n"
                
                # Growth potential assessment
                avg_growth = (revenue_growth + margin_growth + transaction_growth) / 3
                
                if avg_growth > 20:
                    potential = "🔥 HIGH - Strong upward trajectory"
                elif avg_growth > 10:
                    potential = "📈 MODERATE - Steady growth pattern"
                elif avg_growth > 0:
                    potential = "🔄 LOW - Slow growth"
                else:
                    potential = "⚠️ DECLINING - Needs attention"
                
                result += f"💡 Growth Potential: {potential}\n\n"
                
                # Historical trend
                result += f"📅 3-Year Trend:\n"
                for data in historical_data:
                    result += f"   FY{str(data['year'])[2:]}: {format_in_crores(data['revenue'])} "
                    result += f"(GM: {data['gm_percent']:.1f}%)\n"
                
                return result
            
            # 11. OEM performance trend
            elif 'oem performance trend' in query_lower or 'oem trend' in query_lower or 'trend' in query_lower:
                if not year:
                    year = max(self.df['Year_Start'].unique())  # Use latest year if not specified
                
                # Get data for last 3 years
                years = [year-2, year-1, year]
                trend_data = []
                
                for y in years:
                    year_data = self.df[
                        (self.df['Business Manager Name'].str.lower() == business_manager.lower()) &
                        (self.df['Year_Start'] == y)
                    ]
                    
                    if not year_data.empty:
                        oem_year = year_data.groupby('OEM')['TL Base Value'].sum().nlargest(3).to_dict()
                        total_year_revenue = year_data['TL Base Value'].sum()
                        trend_data.append({
                            'year': y,
                            'top_oems': oem_year,
                            'total_revenue': total_year_revenue
                        })
                
                if len(trend_data) < 2:
                    return f"❌ Insufficient data for trend analysis (need at least 2 years)"
                
                result = f"📈 OEM Performance Trend for {business_manager}:\n\n"
                for entry in trend_data:
                    result += f"FY{str(entry['year'])[2:]} (Total: {format_in_crores(entry['total_revenue'])}):\n"
                    for i, (oem_name, revenue) in enumerate(entry['top_oems'].items(), 1):
                        result += f"   {i}. {oem_name}: {format_in_crores(revenue)}\n"
                    result += "\n"
                
                return result
            
            # 12. OEM dependency analysis
            elif 'oem dependency' in query_lower or 'dependency' in query_lower:
                bm_data = self.df[
                    (self.df['Business Manager Name'].str.lower() == business_manager.lower())
                ]
                if year:
                    bm_data = bm_data[bm_data['Year_Start'] == year]
                
                oem_revenues = bm_data.groupby('OEM')['TL Base Value'].sum().sort_values(ascending=False)
                total_revenue_bm = oem_revenues.sum()
                
                if len(oem_revenues) == 0:
                    return f"❌ No OEM data found for {business_manager}"
                
                top_oem_share = (oem_revenues.iloc[0] / total_revenue_bm * 100) if total_revenue_bm > 0 else 0
                top_3_share = (oem_revenues.head(3).sum() / total_revenue_bm * 100) if total_revenue_bm > 0 else 0
                
                result = f"⚖️ OEM Dependency Analysis for {business_manager}"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"📊 Concentration Risk:\n"
                result += f"   • Top OEM Share: {top_oem_share:.1f}%\n"
                result += f"   • Top 3 OEMs Share: {top_3_share:.1f}%\n"
                result += f"   • Total OEMs: {len(oem_revenues)}\n\n"
                
                # Risk assessment
                if top_oem_share > 50:
                    risk_level = "🔴 HIGH"
                elif top_oem_share > 30:
                    risk_level = "🟡 MEDIUM"
                else:
                    risk_level = "🟢 LOW"
                
                result += f"Risk Level: {risk_level} dependency\n\n"
                result += f"Top OEM: {oem_revenues.index[0]} ({top_oem_share:.1f}%)"
                
                return result
            
            # 13. OEM benchmark analysis
            elif 'oem benchmark' in query_lower or 'benchmark' in query_lower:
                if not oem:
                    return "❌ Please specify an OEM for benchmarking"
                
                # Get performance of this OEM across all business managers
                oem_data = self.df[self.df['OEM'].str.lower() == oem.lower()]
                if year:
                    oem_data = oem_data[oem_data['Year_Start'] == year]
                
                bm_performance = oem_data.groupby('Business Manager Name').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_values('TL Base Value', ascending=False)
                
                if bm_performance.empty:
                    return f"❌ No data found for OEM {oem}"
                
                # Find rank of current business manager
                current_rank = None
                for i, bm in enumerate(bm_performance.index, 1):
                    if bm.lower() == business_manager.lower():
                        current_rank = i
                        break
                
                result = f"🏁 OEM {oem} Benchmark"
                if year:
                    result += f" in FY{str(year)[2:]}"
                result += f":\n\n"
                result += f"Business Manager Ranking (by Revenue):\n"
                
                for i, (bm, data) in enumerate(bm_performance.head(5).iterrows(), 1):
                    revenue = data['TL Base Value']
                    margin = data['Gross Margin Value']
                    gm_pct = (margin / revenue * 100) if revenue > 0 else 0
                    
                    prefix = "👑" if i == 1 else f"{i}."
                    highlight = " ← YOU" if bm.lower() == business_manager.lower() else ""
                    
                    result += f"{prefix} {bm}: {format_in_crores(revenue)} (GM: {gm_pct:.1f}%){highlight}\n"
                
                if current_rank and current_rank > 5:
                    result += f"\n{business_manager} ranks #{current_rank} for {oem}"
                
                return result

            # Default case - show basic performance metrics
            else:
                result = f"📊 {business_manager}"
                if oem:
                    result += f" × {oem}"
                if year:
                    result += f" | FY{str(year)[2:]}"
                result += f"\n💰 Revenue: {format_in_crores(total_revenue)}"
                result += f"\n💹 Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                result += f"\n📈 Transactions: {transaction_count:,}"
                return result

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"




    def handle_personnel_oem_query(self, query):
        """Handle personnel-OEM relationship queries"""
        try:
            # Extract personnel role and name
            personnel_roles = [
                'business head', 'group business manager', 'business manager',
                'group channel champ', 'channel champ', 'vertical champ'
            ]
            
            role = None
            person_name = None
            for r in personnel_roles:
                if r in query.lower():
                    role = r.replace(' ', '_')
                    # Try to extract person name
                    role_title = r.title()
                    if role_title in query:
                        # Look for name after role title
                        possible_name = query.split(role_title)[1].strip().split(' ')[0]
                        names = self.processor.get_unique_values(role_title.replace(' ', ''))
                        for name in names:
                            if str(name).lower() == possible_name.lower():
                                person_name = name
                                break
                    break
                    
            if not role or not person_name:
                return None
                
            # Extract OEM if specified
            oem_name = None
            if 'oem' in query.lower():
                for oem in self.oem_stats.keys():
                    if oem.lower() in query.lower():
                        oem_name = oem
                        break
                        
            # Extract year if specified
            year = None
            if 'fy' in query.lower():
                year_part = query.lower().split('fy')[-1][:2]
                year = 2000 + int(year_part)
            elif any(str(y) in query for y in self.yearly_stats.keys()):
                for y in self.yearly_stats.keys():
                    if str(y) in query:
                        year = y
                        break
                        
            # Extract region if specified
            region = None
            if 'region' in query.lower():
                for r in self.df['Region'].unique():
                    if r.lower() in query.lower():
                        region = r
                        break
                        
            # Build the dimension key for pre-computed data
            dim_parts = [role, 'oem']
            if year:
                dim_parts.append('year_start')
            if region:
                dim_parts.append('region')
                
            dim_key = "_".join(dim_parts)
            
            if dim_key not in self.dimension_combinations:
                return None
                
            # Filter the data
            filtered = self.dimension_combinations[dim_key]
            filtered = filtered[filtered[role] == person_name]
            
            if oem_name:
                filtered = filtered[filtered['OEM'] == oem_name]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]
            if region:
                filtered = filtered[filtered['Region'] == region]
                
            if filtered.empty:
                return f"❌ No data found for {role.replace('_', ' ')} {person_name}"
                
            # Determine metric
            if 'gm' in query.lower() or 'margin' in query.lower():
                metric_col = 'Gross Margin Value'
                metric_name = 'Gross Margin'
                if '%' in query or 'gm%' in query.lower():
                    # Calculate GM%
                    filtered['GM%'] = (filtered['Gross Margin Value'] / filtered['TL Base Value']) * 100
                    metric_col = 'GM%'
                    metric_name = 'GM%'
            else:
                metric_col = 'TL Base Value'
                metric_name = 'Revenue'
                
            # Sort and format results
            filtered = filtered.sort_values(metric_col, ascending=False)
            
            result = f"📊 {metric_name} for {role.replace('_', ' ')} {person_name}"
            if oem_name:
                result += f" with OEM {oem_name}"
            if year:
                result += f" in FY{str(year)[2:]}"
            if region:
                result += f" in {region}"
            result += ":\n\n"
            
            if len(filtered) > 1 and 'top' in query.lower():
                # Extract number after "top" more safely
                match = re.search(r'top\s+(\d+)', query.lower())
                if match:
                    try:
                        top_n = int(match.group(1))
                        filtered = filtered.head(top_n)
                    except (ValueError, AttributeError):
                        filtered = filtered.head(5)
                else:
                    # If "top" is mentioned but no number found, default to 5
                    filtered = filtered.head(5)
                    
            for _, row in filtered.iterrows():
                value = row[metric_col]
                if metric_col == 'GM%':
                    value_str = f"{value:.1f}%"
                else:
                    value_str = format_in_crores(value)
                    
                parts = [f"OEM: {row['OEM']}"]
                if year:
                    parts.append(f"FY{str(row['Year_Start'])[2:]}")
                if region:
                    parts.append(f"Region: {row['Region']}")
                    
                result += f"   • {' | '.join(parts)}: {value_str}\n"
                
            # Add visualization if requested
            if 'show' in query.lower() and len(filtered) > 1:
                self.create_visualization('personnel_oem', {
                    'person_name': person_name,
                    'role': role
                })
                
            return result
            
        except Exception as e:
            print(f"Error in personnel-OEM query: {e}")
            return None
        
    def _calculate_vertical_champ_growth(self, champ_name, year):
        """Calculate growth metrics for a Vertical Champ compared to the previous year"""
        try:
            if not year:
                return None
                
            prev_year = year - 1
            current_data = self.df[
                (self.df['Vertical Champ'].str.lower() == champ_name.lower()) & 
                (self.df['Year_Start'] == year)
            ]
            prev_data = self.df[
                (self.df['Vertical Champ'].str.lower() == champ_name.lower()) & 
                (self.df['Year_Start'] == prev_year)
            ]
            
            if len(prev_data) == 0 or len(current_data) == 0:
                return None
                
            current_revenue = current_data['TL Base Value'].sum()
            prev_revenue = prev_data['TL Base Value'].sum()
            revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            current_margin = current_data['Gross Margin Value'].sum()
            prev_margin = prev_data['Gross Margin Value'].sum()
            margin_growth = ((current_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
            
            current_count = len(current_data)
            prev_count = len(prev_data)
            count_growth = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
            
            return {
                'revenue_growth': revenue_growth,
                'margin_growth': margin_growth,
                'transaction_growth': count_growth,
                'prev_year': prev_year,
                'current_year': year
            }
        except Exception as e:
            print(f"Error calculating growth: {e}")
            return None
    
    def handle_personnel_partner_query(self, query):
        """Handle personnel-partner relationship queries"""
        try:
            # Extract personnel role and name
            personnel_roles = [
                'business head', 'group business manager', 'business manager',
                'group channel champ', 'channel champ', 'vertical champ'
            ]
            
            role = None
            person_name = None
            for r in personnel_roles:
                if r in query.lower():
                    role = r.replace(' ', '_')
                    # Try to extract person name
                    role_title = r.title()
                    if role_title in query:
                        # Look for name after role title
                        possible_name = query.split(role_title)[1].strip().split(' ')[0]
                        names = self.processor.get_unique_values(role_title.replace(' ', ''))
                        for name in names:
                            if str(name).lower() == possible_name.lower():
                                person_name = name
                                break
                    break
                    
            if not role or not person_name:
                return None
                
            # Extract Partner if specified
            partner_name = None
            if 'partner' in query.lower():
                for partner in self.partner_stats.keys():
                    if partner.lower() in query.lower():
                        partner_name = partner
                        break
                        
            # Extract year if specified
            year = None
            if 'fy' in query.lower():
                year_part = query.lower().split('fy')[-1][:2]
                year = 2000 + int(year_part)
            elif any(str(y) in query for y in self.yearly_stats.keys()):
                for y in self.yearly_stats.keys():
                    if str(y) in query:
                        year = y
                        break
                        
            # Extract region if specified
            region = None
            if 'region' in query.lower():
                for r in self.df['Region'].unique():
                    if r.lower() in query.lower():
                        region = r
                        break
                        
            # Build the dimension key for pre-computed data
            dim_parts = [role, 'partner']
            if year:
                dim_parts.append('year_start')
            if region:
                dim_parts.append('region')
                
            dim_key = "_".join(dim_parts)
            
            if dim_key not in self.dimension_combinations:
                return None
                
            # Filter the data
            filtered = self.dimension_combinations[dim_key]
            filtered = filtered[filtered[role] == person_name]
            
            if partner_name:
                filtered = filtered[filtered['Partner'] == partner_name]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]
            if region:
                filtered = filtered[filtered['Region'] == region]
                
            if filtered.empty:
                return f"❌ No data found for {role.replace('_', ' ')} {person_name}"
                
            # Determine metric
            if 'gm' in query.lower() or 'margin' in query.lower():
                metric_col = 'Gross Margin Value'
                metric_name = 'Gross Margin'
                if '%' in query or 'gm%' in query.lower():
                    # Calculate GM%
                    filtered['GM%'] = (filtered['Gross Margin Value'] / filtered['TL Base Value']) * 100
                    metric_col = 'GM%'
                    metric_name = 'GM%'
            else:
                metric_col = 'TL Base Value'
                metric_name = 'Revenue'
                
            # Sort and format results
            filtered = filtered.sort_values(metric_col, ascending=False)
            
            result = f"📊 {metric_name} for {role.replace('_', ' ')} {person_name}"
            if partner_name:
                result += f" with Partner {partner_name}"
            if year:
                result += f" in FY{str(year)[2:]}"
            if region:
                result += f" in {region}"
            result += ":\n\n"
            
            if len(filtered) > 1 and 'top' in query.lower():
                # Fix: Check if re.search returns a match before calling .group()
                match = re.search(r'top (\d+)', query.lower())
                if match:
                    top_n = int(match.group(1))
                    filtered = filtered.head(top_n)
                else:
                    filtered = filtered.head(5)
                    
            for _, row in filtered.iterrows():
                value = row[metric_col]
                if metric_col == 'GM%':
                    value_str = f"{value:.1f}%"
                else:
                    value_str = format_in_crores(value)
                    
                parts = [f"Partner: {row['Partner']}"]
                if year:
                    parts.append(f"FY{str(row['Year_Start'])[2:]}")
                if region:
                    parts.append(f"Region: {row['Region']}")
                    
                result += f"   • {' | '.join(parts)}: {value_str}\n"
                
            # Add visualization if requested
            if 'show' in query.lower() and len(filtered) > 1:
                self.create_visualization('personnel_partner', {
                    'person_name': person_name,
                    'role': role
                })
                
            return result
            
        except Exception as e:
            print(f"Error in personnel-partner query: {e}")
            return None
        
    def handle_oem_partner_customer_query(self, query):
        """Handle OEM+Partner+Customer relationship queries"""
        try:
            # Extract OEM, Partner, Customer names
            oem_name, partner_name, customer_name = None, None, None
            
            for oem in self.oem_stats.keys():
                if oem.lower() in query.lower():
                    oem_name = oem
                    break
                    
            for partner in self.partner_stats.keys():
                if partner.lower() in query.lower():
                    partner_name = partner
                    break
                    
            for customer in self.customer_stats.keys():
                if customer.lower() in query.lower():
                    customer_name = customer
                    break
                    
            # Extract year if specified
            year = None
            if 'fy' in query.lower():
                year_part = query.lower().split('fy')[-1][:2]
                year = 2000 + int(year_part)
                
            # Extract region if specified
            region = None
            if 'region' in query.lower():
                for r in self.df['Region'].unique():
                    if r.lower() in query.lower():
                        region = r
                        break
                        
            # Build dimension key
            dim_parts = []
            if oem_name:
                dim_parts.append('oem')
            if partner_name:
                dim_parts.append('partner')
            if customer_name:
                dim_parts.append('end customer')
            if year:
                dim_parts.append('year_start')
            if region:
                dim_parts.append('region')
                
            dim_key = "_".join(dim_parts)
            
            if dim_key not in self.dimension_combinations:
                return None
                
            # Filter data
            filtered = self.dimension_combinations[dim_key]
            if oem_name:
                filtered = filtered[filtered['OEM'] == oem_name]
            if partner_name:
                filtered = filtered[filtered['Partner'] == partner_name]
            if customer_name:
                filtered = filtered[filtered['End Customer'] == customer_name]
            if year:
                filtered = filtered[filtered['Year_Start'] == year]
            if region:
                filtered = filtered[filtered['Region'] == region]
                
            if filtered.empty:
                return "❌ No data matches your criteria"
                
            # Determine metric
            if 'gm' in query.lower() or 'margin' in query.lower():
                metric_col = 'Gross Margin Value'
                metric_name = 'Gross Margin'
                if '%' in query or 'gm%' in query.lower():
                    filtered['GM%'] = (filtered['Gross Margin Value'] / filtered['TL Base Value']) * 100
                    metric_col = 'GM%'
                    metric_name = 'GM%'
            else:
                metric_col = 'TL Base Value'
                metric_name = 'Revenue'
                
            # Format results
            result = "📊 "
            parts = []
            if oem_name:
                parts.append(f"OEM: {oem_name}")
            if partner_name:
                parts.append(f"Partner: {partner_name}")
            if customer_name:
                parts.append(f"Customer: {customer_name}")
            if year:
                parts.append(f"FY{str(year)[2:]}")
            if region:
                parts.append(f"Region: {region}")
                
            result += " + ".join(parts) + f" - {metric_name}:\n\n"
            
            for _, row in filtered.iterrows():
                value = row[metric_col]
                if metric_col == 'GM%':
                    value_str = f"{value:.1f}%"
                else:
                    value_str = format_in_crores(value)
                    
                result += f"   • {value_str}\n"
                
            # Add growth comparison if requested
            if 'growth' in query.lower() and year:
                prev_year = year - 1
                if prev_year in self.yearly_stats:
                    # Compare with previous year
                    pass
                    
            return result
            
        except Exception as e:
            print(f"Error in OEM+Partner+Customer query: {e}")
            return None

    def process_query(self, user_query):
        """Process user query using only the specified handler methods"""
        # Store original query for name extraction
        original_query = user_query
        # Replace shorthand terms in the query
        user_query_lower = user_query.lower()
        user_query = user_query.replace('gm', 'gross margin').replace('tl', 'tl base value')

        print(f"DEBUG MAIN: Processing query: '{original_query}'")
        print(f"DEBUG MAIN: Query lowercase: '{user_query_lower}'")
        
        # Debug: Check what each detection method returns
        print(f"DEBUG MAIN: _is_vertical_champ_query returns: {self._is_vertical_champ_query(user_query_lower)}")
        print(f"DEBUG MAIN: Contains 'vertical champ': {'vertical champ' in user_query_lower}")
        print(f"DEBUG MAIN: Contains 'customer': {any(term in user_query_lower for term in ['end customer', 'customer'])}")

        # PRIORITY 0: Handle special commands like table generation
        if user_query.startswith("generate regional performance table for"):
            year_string = user_query.replace("generate regional performance table for", "").strip()
            return self.get_yearly_regional_performance_table(year_string)

        # PRIORITY 1: Direct Entity Queries with Explicit Keywords (HIGH PRIORITY)
        
        # Channel queries - HIGHEST PRIORITY when "channel" keyword is present
        if 'channel' in user_query_lower and not any(term in user_query_lower for term in ['channel champ', 'group channel champ']):
            print("DEBUG MAIN: Detected explicit channel query (highest priority)")
            result = self.handle_channel_query(user_query)
            if self._is_valid_result(result):
                return result

        # Partner queries - HIGH PRIORITY when "partner" keyword is present
        if 'partner' in user_query_lower and not any(term in user_query_lower for term in ['channel champ', 'group channel champ']):
            print("DEBUG MAIN: Detected explicit partner query (high priority)")
            result = self.handle_partner_query(user_query)
            if self._is_valid_result(result):
                return result

        # OEM queries - HIGH PRIORITY when "oem" keyword is present
        if 'oem' in user_query_lower and not any(term in user_query_lower for term in ['business head', 'business manager', 'group business manager']):
            print("DEBUG MAIN: Detected explicit OEM query (high priority)")
            result = self.handle_oem_query(user_query)
            if self._is_valid_result(result):
                return result

        # Region queries - HIGH PRIORITY when "region" keyword is present
        if 'region' in user_query_lower:
            print("DEBUG MAIN: Detected explicit region query (high priority)")
            result = self.handle_region_query(user_query)
            if self._is_valid_result(result):
                return result

        # End Customer queries - HIGH PRIORITY when customer keywords are present
        # TEMPORARY DEBUG VERSION
        if any(term in user_query_lower for term in ['end customer', 'customer']) and not any(term in user_query_lower for term in ['vertical champ', 'champ']):
            print("DEBUG MAIN: Detected explicit end customer query (high priority)")
            result = self.handle_end_customer_query(user_query)
            print(f"DEBUG MAIN: End customer handler returned: {result[:500] if result else 'None'}")
            print(f"DEBUG MAIN: Result type: {type(result)}")
            print(f"DEBUG MAIN: Result starts with ❌: {result.startswith('❌') if isinstance(result, str) else 'N/A'}")
            print(f"DEBUG MAIN: Result validation: {self._is_valid_result(result)}")
            # TEMPORARY: Return result regardless of validation to see what we're getting
            return result

        # PRIORITY 2: Personnel + Entity Combination Queries (1-6)
        
        # 1) Business Head Name <-> OEM
        if ('business head' in user_query_lower and 'oem' in user_query_lower) or \
        self._contains_business_head_and_oem(user_query_lower):
            print("DEBUG MAIN: Detected business head + OEM query")
            result = self.handle_business_head_oem_query(user_query)
            if self._is_valid_result(result):
                return result

        # 2) Group Business Manager Name <-> OEM
        if ('group business manager' in user_query_lower and 'oem' in user_query_lower) or \
        self._contains_group_business_manager_and_oem(user_query_lower):
            print("DEBUG MAIN: Detected group business manager + OEM query")
            result = self.handle_group_business_manager_oem_query(user_query)
            if self._is_valid_result(result):
                return result

        # 3) Business Manager Name <-> OEM
        if ('business manager' in user_query_lower and 'oem' in user_query_lower and 
            'group business manager' not in user_query_lower) or \
        self._contains_business_manager_and_oem(user_query_lower):
            print("DEBUG MAIN: Detected business manager + OEM query")
            result = self.handle_business_manager_oem_query(user_query)
            if self._is_valid_result(result):
                return result

        # 4) Group Channel Champ <-> Partner
        if ('group channel champ' in user_query_lower and 'partner' in user_query_lower) or \
        self._contains_group_channel_champ_and_partner(user_query_lower):
            print("DEBUG MAIN: Detected group channel champ + partner query")
            result = self.handle_group_channel_champ_partner_query(user_query)
            if self._is_valid_result(result):
                return result

        # 5) Channel Champ <-> Partner
        if ('channel champ' in user_query_lower and 'partner' in user_query_lower and 
            'group channel champ' not in user_query_lower) or \
        self._contains_channel_champ_and_partner(user_query_lower):
            print("DEBUG MAIN: Detected channel champ + partner query")
            result = self.handle_channel_champ_partner_query(user_query)
            if self._is_valid_result(result):
                return result

        # 6) Vertical Champ <-> End Customer Name
        if ('vertical champ' in user_query_lower and 
            any(term in user_query_lower for term in ['end customer', 'customer'])) or \
        self._contains_vertical_champ_and_customer(user_query_lower):
            print("DEBUG MAIN: Detected vertical champ + customer query")
            result = self.handle_vertical_champ_customer_query(user_query)
            if self._is_valid_result(result):
                return result

        # PRIORITY 3: Personnel Queries (12-17)
        
        # 12) Vertical Champ queries
        if self._is_vertical_champ_query(user_query_lower):
            print("DEBUG MAIN: Detected vertical champ query")
            result = self.handle_vertical_champ_query(original_query)
            if self._is_valid_result(result):
                return result
        
        # Additional fallback for vertical champ queries that might not be caught
        elif 'vertical champ' in user_query_lower:
            print("DEBUG MAIN: Fallback vertical champ detection")
            result = self.handle_vertical_champ_query(original_query)
            if self._is_valid_result(result):
                return result

        # 13) Business Manager queries
        if self._is_business_manager_query(user_query_lower):
            print("DEBUG MAIN: Detected business manager query")
            result = self.handle_business_manager_query(user_query)
            if self._is_valid_result(result):
                return result

        # 14) Group Channel Champ queries
        if self._is_group_channel_champ_query(user_query_lower):
            print("DEBUG MAIN: Detected group channel champ query")
            result = self.handle_group_channel_champ_query(original_query)
            if self._is_valid_result(result):
                return result

        # 15) Group Business Manager queries
        if self._is_group_business_manager_query(user_query_lower):
            print("DEBUG MAIN: Detected group business manager query")
            result = self.handle_group_business_manager_query(user_query)
            if self._is_valid_result(result):
                return result

        # 16) Channel Champ queries
        if self._is_channel_champ_query(user_query_lower):
            print("DEBUG MAIN: Detected channel champ query")
            result = self.handle_channel_champ_query(user_query)
            if self._is_valid_result(result):
                return result

        # 17) Business Head queries
        if self._is_business_head_query(user_query_lower):
            print("DEBUG MAIN: Detected business head query")
            result = self.handle_business_head_query(user_query)
            if self._is_valid_result(result):
                return result

        # PRIORITY 4: Remaining Direct Entity Queries (Fallback)
        
        # Channel queries (fallback for name-only detection)
        if self._is_channel_query(user_query_lower):
            print("DEBUG MAIN: Detected channel query (fallback)")
            result = self.handle_channel_query(user_query)
            if self._is_valid_result(result):
                return result

        # Vertical queries - FIXED to be more specific
        if self._is_vertical_query(user_query_lower):
            print("DEBUG MAIN: Detected vertical query")
            result = self.handle_vertical_query(user_query)
            if self._is_valid_result(result):
                return result

        # Partner queries (fallback)
        if self._is_partner_query(user_query_lower):
            print("DEBUG MAIN: Detected partner query (fallback)")
            result = self.handle_partner_query(user_query)
            if self._is_valid_result(result):
                return result

        # End Customer queries (fallback) - ADDED MORE DEBUG
        if self._is_end_customer_query(user_query_lower):
            print("DEBUG MAIN: Detected end customer query (fallback)")
            result = self.handle_end_customer_query(user_query)
            print(f"DEBUG MAIN: Fallback end customer result: {result[:200] if result else 'None'}")
            if self._is_valid_result(result):
                return result

        # OEM queries (fallback)
        if self._is_oem_query(user_query_lower):
            print("DEBUG MAIN: Detected OEM query (fallback)")
            result = self.handle_oem_query(user_query)
            if self._is_valid_result(result):
                return result

        # Region queries (fallback for name-only detection)
        if self._is_region_query(user_query_lower):
            print("DEBUG MAIN: Detected region query (fallback)")
            result = self.handle_region_query(user_query)
            if self._is_valid_result(result):
                return result

        # If no handler matches, return error message
        print("DEBUG MAIN: No handler matched the query")
        return "❌ Unable to process query. Please check your query format and try again."

    # Helper methods for query detection
    def _is_valid_result(self, result):
        """Check if result is valid (not None, not empty, not error)"""
        return result and isinstance(result, str) and not result.startswith("❌")

    def _contains_business_head_and_oem(self, query_lower):
        """Check if query contains both business head and OEM references"""
        business_head_terms = ['business head', 'bh']
        oem_terms = ['oem']
        
        has_business_head = any(term in query_lower for term in business_head_terms)
        has_oem = any(term in query_lower for term in oem_terms)
        
        # CRITICAL FIX: If query explicitly mentions "channel", it's likely a channel query, not personnel
        if 'channel' in query_lower:
            print(f"DEBUG: _contains_business_head_and_oem - Found 'channel' keyword, skipping name matching")
            return has_business_head and has_oem
        
        # Also check for actual names from data - but be more careful
        if hasattr(self, 'df') and self.df is not None:
            try:
                # Check for business head names - but only if we already have business head terms
                if has_business_head and 'Business Head Name' in self.df.columns:
                    business_head_names = [str(name).lower() for name in self.df['Business Head Name'].dropna().unique() if pd.notna(name) and len(str(name)) > 2]
                    has_business_head = has_business_head or any(name in query_lower for name in business_head_names)
                
                # Check for OEM names - but only if we already have OEM terms
                if has_oem and 'OEM' in self.df.columns:
                    oem_names = [str(oem).lower() for oem in self.df['OEM'].dropna().unique() if pd.notna(oem) and len(str(oem)) > 2]
                    has_oem = has_oem or any(oem in query_lower for oem in oem_names)
            except Exception as e:
                print(f"DEBUG: Error checking business head + OEM names: {e}")
        
        result = has_business_head and has_oem
        print(f"DEBUG: _contains_business_head_and_oem - has_business_head: {has_business_head}, has_oem: {has_oem}, result: {result}")
        return result

    def _contains_group_business_manager_and_oem(self, query_lower):
        """Check if query contains both group business manager and OEM references"""
        gbm_terms = ['group business manager', 'gbm']
        oem_terms = ['oem']
        
        has_gbm = any(term in query_lower for term in gbm_terms)
        has_oem = any(term in query_lower for term in oem_terms)
        
        # CRITICAL FIX: If query explicitly mentions "channel", it's likely a channel query
        if 'channel' in query_lower:
            print(f"DEBUG: _contains_group_business_manager_and_oem - Found 'channel' keyword, skipping name matching")
            return has_gbm and has_oem
        
        # Also check for actual names from data - but be more careful
        if hasattr(self, 'df') and self.df is not None:
            try:
                if has_gbm and 'Group Business Manager Name' in self.df.columns:
                    gbm_names = [str(name).lower() for name in self.df['Group Business Manager Name'].dropna().unique() if pd.notna(name) and len(str(name)) > 2]
                    has_gbm = has_gbm or any(name in query_lower for name in gbm_names)
                
                if has_oem and 'OEM' in self.df.columns:
                    oem_names = [str(oem).lower() for oem in self.df['OEM'].dropna().unique() if pd.notna(oem) and len(str(oem)) > 2]
                    has_oem = has_oem or any(oem in query_lower for oem in oem_names)
            except Exception as e:
                print(f"DEBUG: Error checking GBM + OEM names: {e}")
        
        result = has_gbm and has_oem
        print(f"DEBUG: _contains_group_business_manager_and_oem - has_gbm: {has_gbm}, has_oem: {has_oem}, result: {result}")
        return result

    def _contains_business_manager_and_oem(self, query_lower):
        """Check if query contains both business manager and OEM references"""
        bm_terms = ['business manager', 'bm']
        oem_terms = ['oem']
        
        # Exclude group business manager
        if 'group business manager' in query_lower:
            return False
        
        has_bm = any(term in query_lower for term in bm_terms)
        has_oem = any(term in query_lower for term in oem_terms)
        
        # CRITICAL FIX: If query explicitly mentions "channel", it's likely a channel query
        if 'channel' in query_lower:
            print(f"DEBUG: _contains_business_manager_and_oem - Found 'channel' keyword, skipping name matching")
            return has_bm and has_oem
        
        # Also check for actual names from data - but be more careful
        if hasattr(self, 'df') and self.df is not None:
            try:
                if has_bm and 'Business Manager Name' in self.df.columns:
                    bm_names = [str(name).lower() for name in self.df['Business Manager Name'].dropna().unique() if pd.notna(name) and len(str(name)) > 2]
                    has_bm = has_bm or any(name in query_lower for name in bm_names)
                
                if has_oem and 'OEM' in self.df.columns:
                    oem_names = [str(oem).lower() for oem in self.df['OEM'].dropna().unique() if pd.notna(oem) and len(str(oem)) > 2]
                    has_oem = has_oem or any(oem in query_lower for oem in oem_names)
            except Exception as e:
                print(f"DEBUG: Error checking BM + OEM names: {e}")
        
        result = has_bm and has_oem
        print(f"DEBUG: _contains_business_manager_and_oem - has_bm: {has_bm}, has_oem: {has_oem}, result: {result}")
        return result

    def _contains_group_channel_champ_and_partner(self, query_lower):
        """Check if query contains both group channel champ and partner references"""
        gcc_terms = ['group channel champ', 'gcc']
        partner_terms = ['partner']
        
        has_gcc = any(term in query_lower for term in gcc_terms)
        has_partner = any(term in query_lower for term in partner_terms)
        
        # CRITICAL FIX: If query explicitly mentions "channel" without champ, it's likely a direct channel query
        if 'channel' in query_lower and 'champ' not in query_lower:
            print(f"DEBUG: _contains_group_channel_champ_and_partner - Found 'channel' without 'champ', skipping name matching")
            return has_gcc and has_partner
        
        # Also check for actual names from data
        if hasattr(self, 'df') and self.df is not None:
            try:
                if has_gcc and 'Group Channel Champ' in self.df.columns:
                    gcc_names = [str(name).lower() for name in self.df['Group Channel Champ'].dropna().unique() if pd.notna(name) and len(str(name)) > 2]
                    has_gcc = has_gcc or any(name in query_lower for name in gcc_names)
                
                if has_partner and 'Partner' in self.df.columns:
                    partner_names = [str(partner).lower() for partner in self.df['Partner'].dropna().unique() if pd.notna(partner) and len(str(partner)) > 2]
                    has_partner = has_partner or any(partner in query_lower for partner in partner_names)
            except Exception as e:
                print(f"DEBUG: Error checking GCC + Partner names: {e}")
        
        result = has_gcc and has_partner
        print(f"DEBUG: _contains_group_channel_champ_and_partner - has_gcc: {has_gcc}, has_partner: {has_partner}, result: {result}")
        return result

    def _contains_channel_champ_and_partner(self, query_lower):
        """Check if query contains both channel champ and partner references"""
        cc_terms = ['channel champ', 'cc']
        partner_terms = ['partner']
        
        # Exclude group channel champ
        if 'group channel champ' in query_lower:
            return False
        
        has_cc = any(term in query_lower for term in cc_terms)
        has_partner = any(term in query_lower for term in partner_terms)
        
        # CRITICAL FIX: Remove this problematic logic that's blocking the detection
        # The original code was returning early if 'channel' was found without 'champ'
        # This was preventing proper detection when both are present
        
        # Also check for actual names from data
        if hasattr(self, 'df') and self.df is not None:
            try:
                # Check for Channel Champs (try both possible column names)
                if 'Channel Champ' in self.df.columns:
                    cc_names = [str(name).lower() for name in self.df['Channel Champ'].dropna().unique() 
                            if pd.notna(name) and len(str(name)) > 2]
                    has_cc_name = any(name in query_lower for name in cc_names)
                    has_cc = has_cc or has_cc_name
                elif 'Channel Champ' in self.df.columns:
                    cc_names = [str(name).lower() for name in self.df['Channel Champ'].dropna().unique() 
                            if pd.notna(name) and len(str(name)) > 2]
                    has_cc_name = any(name in query_lower for name in cc_names)
                    has_cc = has_cc or has_cc_name
                
                # Check for Partner names
                if 'Partner' in self.df.columns:
                    partner_names = [str(partner).lower() for partner in self.df['Partner'].dropna().unique() 
                                if pd.notna(partner) and len(str(partner)) > 2]
                    has_partner_name = any(partner in query_lower for partner in partner_names)
                    has_partner = has_partner or has_partner_name
            except Exception as e:
                print(f"DEBUG: Error checking CC + Partner names: {e}")
        
        result = has_cc and has_partner
        print(f"DEBUG: _contains_channel_champ_and_partner - has_cc: {has_cc}, has_partner: {has_partner}, result: {result}")
        return result

    def _contains_vertical_champ_and_customer(self, query_lower):
        """Check if query contains both vertical champ and customer references"""
        vc_terms = ['vertical champ', 'vc']
        customer_terms = ['end customer', 'customer']
        
        has_vc = any(term in query_lower for term in vc_terms)
        has_customer = any(term in query_lower for term in customer_terms)
        
        # CRITICAL FIX: If query explicitly mentions "channel", it's likely a channel query
        if 'channel' in query_lower:
            print(f"DEBUG: _contains_vertical_champ_and_customer - Found 'channel' keyword, skipping name matching")
            return has_vc and has_customer
        
        # Also check for actual names from data
        if hasattr(self, 'df') and self.df is not None:
            try:
                if has_vc and 'Vertical Champ' in self.df.columns:
                    vc_names = [str(name).lower() for name in self.df['Vertical Champ'].dropna().unique() if pd.notna(name) and len(str(name)) > 2]
                    has_vc = has_vc or any(name in query_lower for name in vc_names)
                
                if has_customer and 'End Customer Name' in self.df.columns:
                    customer_names = [str(customer).lower() for customer in self.df['End Customer Name'].dropna().unique() if pd.notna(customer) and len(str(customer)) > 2]
                    has_customer = has_customer or any(customer in query_lower for customer in customer_names)
            except Exception as e:
                print(f"DEBUG: Error checking VC + Customer names: {e}")
        
        result = has_vc and has_customer
        print(f"DEBUG: _contains_vertical_champ_and_customer - has_vc: {has_vc}, has_customer: {has_customer}, result: {result}")
        return result

    def _is_vertical_champ_query(self, query_lower):
        """Check if this is a vertical champ query - FIXED TO BE MORE SPECIFIC"""
        # First check for explicit vertical champ terms
        vc_terms = ['vertical champ', 'vc']
        has_vc_term = any(term in query_lower for term in vc_terms)
        
        # CRITICAL FIX: Only check for vertical champ names if we have explicit VC terms
        # OR if the query doesn't contain other entity indicators
        has_vc_name = False
        
        # Check if query has other entity keywords that should take precedence
        other_entity_terms = ['channel', 'partner', 'oem', 'business head', 'business manager', 'region']
        has_other_entity = any(term in query_lower for term in other_entity_terms)
        
        # Only do name matching if we have explicit VC terms OR no other entity terms
        if has_vc_term or not has_other_entity:
            if hasattr(self, 'df') and self.df is not None:
                try:
                    vc_columns = ['Vertical Champ', 'Vertical Champ Name']
                    for col in vc_columns:
                        if col in self.df.columns:
                            vc_names = [str(name).lower() for name in self.df[col].dropna().unique() if pd.notna(name)]
                            # IMPROVED: Check for exact word matches to avoid false positives
                            for name in vc_names:
                                # Use word boundary matching for better precision
                                pattern = r'\b' + re.escape(name) + r'\b'
                                if re.search(pattern, query_lower):
                                    has_vc_name = True
                                    break
                            if has_vc_name:
                                break
                except Exception as e:
                    print(f"DEBUG: Error checking vertical champ names: {e}")
        
        # Return True only if we have explicit terms OR (name match AND no other entity keywords)
        is_vc_query = has_vc_term or (has_vc_name and not has_other_entity)
        
        # CRITICAL: Exclude if this should be handled by combination handlers
        if is_vc_query:
            # Check if this is a combination query that should be handled elsewhere
            customer_terms = ['end customer', 'customer']
            has_customer = any(term in query_lower for term in customer_terms)
            
            if has_customer:
                # This should be handled by vertical champ + customer combination handler
                return False
        
        print(f"DEBUG: _is_vertical_champ_query - has_vc_term: {has_vc_term}, has_vc_name: {has_vc_name}, has_other_entity: {has_other_entity}, result: {is_vc_query}")
        return is_vc_query

    def _is_vertical_query(self, query_lower):
        """Check if this is a direct vertical query - FIXED TO EXCLUDE VERTICAL CHAMP"""
        vertical_terms = ['vertical account', 'account enterprises']  # REMOVED 'vertical' alone
        
        has_vertical = any(term in query_lower for term in vertical_terms)
        
        # CRITICAL: Exclude anything with 'champ' in it
        if 'champ' in query_lower:
            return False
        
        # CRITICAL: Exclude 'vertical champ' specifically
        if 'vertical champ' in query_lower:
            return False
        
        # Also check for actual vertical names, but only if no champ terms
        if hasattr(self, 'df') and self.df is not None and 'Vertical Account' in self.df.columns:
            try:
                vertical_names = [str(vertical).lower() for vertical in self.df['Vertical Account'].dropna().unique() if pd.notna(vertical)]
                has_vertical = has_vertical or any(vertical in query_lower for vertical in vertical_names)
            except Exception as e:
                print(f"DEBUG: Error checking vertical names: {e}")
        
        print(f"DEBUG: _is_vertical_query - result: {has_vertical}")
        return has_vertical

    def _is_partner_query(self, query_lower):
        """Check if this is a direct partner query"""
        partner_terms = ['partner']
        # Exclude personnel + partner combinations already handled above
        exclude_terms = ['channel champ', 'group channel champ']
        
        has_partner = any(term in query_lower for term in partner_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual partner names
        if hasattr(self, 'df') and self.df is not None and 'Partner' in self.df.columns:
            try:
                partner_names = [str(partner).lower() for partner in self.df['Partner'].dropna().unique() if pd.notna(partner)]
                has_partner = has_partner or any(partner in query_lower for partner in partner_names)
            except Exception as e:
                print(f"DEBUG: Error checking partner names: {e}")
        
        return has_partner and not has_exclude

    def _is_end_customer_query(self, query_lower):
        """Check if this is a direct end customer query"""
        customer_terms = ['end customer', 'customer name', 'customer']
        # Exclude vertical champ + customer combinations already handled above
        exclude_terms = ['vertical champ', 'champ']
        
        has_customer = any(term in query_lower for term in customer_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual customer names
        if hasattr(self, 'df') and self.df is not None and 'End Customer Name' in self.df.columns:
            try:
                customer_names = [str(customer).lower() for customer in self.df['End Customer Name'].dropna().unique() if pd.notna(customer)]
                has_customer = has_customer or any(customer in query_lower for customer in customer_names)
            except Exception as e:
                print(f"DEBUG: Error checking customer names: {e}")
        
        return has_customer and not has_exclude

    def _is_channel_query(self, query_lower):
        """Check if this is a direct channel query - IMPROVED"""
        channel_terms = ['channel']
        # Exclude personnel + channel combinations already handled above
        exclude_terms = ['channel champ', 'group channel champ']
        
        has_channel = any(term in query_lower for term in channel_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # IMPROVED: Better channel name detection
        has_channel_name = False
        if hasattr(self, 'df') and self.df is not None and 'Channel' in self.df.columns:
            try:
                channel_names = [str(channel).lower() for channel in self.df['Channel'].dropna().unique() if pd.notna(channel)]
                
                # CRITICAL FIX: Only check for meaningful channel names, exclude problematic ones
                meaningful_channels = [name for name in channel_names if len(name) > 1 and name != '-']
                
                print(f"DEBUG _is_channel_query: All channels: {channel_names}")
                print(f"DEBUG _is_channel_query: Meaningful channels: {meaningful_channels}")
                
                # Use word boundary matching for meaningful channel names to avoid false positives
                for channel_name in meaningful_channels:
                    if '-' in channel_name:
                        # For hyphenated channels like "tier-1", use lookbehind/lookahead
                        escaped_channel = re.escape(channel_name)
                        pattern = r'(?<![a-zA-Z0-9])' + escaped_channel + r'(?![a-zA-Z0-9])'
                        if re.search(pattern, query_lower):
                            has_channel_name = True
                            print(f"DEBUG _is_channel_query: Found hyphenated channel match: {channel_name}")
                            break
                    else:
                        # For regular channels, use word boundaries
                        pattern = r'\b' + re.escape(channel_name) + r'\b'
                        if re.search(pattern, query_lower):
                            has_channel_name = True
                            print(f"DEBUG _is_channel_query: Found regular channel match: {channel_name}")
                            break
                
            except Exception as e:
                print(f"DEBUG: Error checking channel names: {e}")
        
        # IMPROVED: Prioritize explicit 'channel' keyword over just name matching
        result = (has_channel or has_channel_name) and not has_exclude
        
        print(f"DEBUG: _is_channel_query - has_channel: {has_channel}, has_channel_name: {has_channel_name}, has_exclude: {has_exclude}, result: {result}")
        return result

    def _is_oem_query(self, query_lower):
        """Check if this is a direct OEM query"""
        oem_terms = ['oem']
        # Exclude personnel + OEM combinations already handled above
        exclude_terms = ['business head', 'business manager', 'group business manager']
        
        has_oem = any(term in query_lower for term in oem_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual OEM names
        if hasattr(self, 'df') and self.df is not None and 'OEM' in self.df.columns:
            try:
                oem_names = [str(oem).lower() for oem in self.df['OEM'].dropna().unique() if pd.notna(oem)]
                has_oem = has_oem or any(oem in query_lower for oem in oem_names)
            except Exception as e:
                print(f"DEBUG: Error checking OEM names: {e}")
        
        return has_oem and not has_exclude

    def _is_region_query(self, query_lower):
        """Check if this is a direct region query"""
        region_terms = ['region']
        
        has_region = any(term in query_lower for term in region_terms)
        
        # Also check for actual region names
        if hasattr(self, 'df') and self.df is not None and 'Region' in self.df.columns:
            try:
                region_names = [str(region).lower() for region in self.df['Region'].dropna().unique() if pd.notna(region)]
                # Use word boundary matching for better precision
                for region_name in region_names:
                    pattern = r'\b' + re.escape(region_name) + r'\b'
                    if re.search(pattern, query_lower):
                        has_region = True
                        print(f"DEBUG _is_region_query: Found region match: {region_name}")
                        break
            except Exception as e:
                print(f"DEBUG: Error checking region names: {e}")
        
        print(f"DEBUG: _is_region_query - result: {has_region}")
        return has_region

    def _is_business_manager_query(self, query_lower):
        """Check if this is a business manager query"""
        bm_terms = ['business manager']
        # Exclude combinations already handled above
        exclude_terms = ['group business manager', 'business head', 'oem']
        
        has_bm = any(term in query_lower for term in bm_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual business manager names
        if hasattr(self, 'df') and self.df is not None and 'Business Manager Name' in self.df.columns:
            try:
                bm_names = [str(name).lower() for name in self.df['Business Manager Name'].dropna().unique() if pd.notna(name)]
                has_bm = has_bm or any(name in query_lower for name in bm_names)
            except Exception as e:
                print(f"DEBUG: Error checking business manager names: {e}")
        
        return has_bm and not has_exclude

    def _is_group_channel_champ_query(self, query_lower):
        """Check if this is a group channel champ query"""
        gcc_terms = ['group channel champ', 'gcc']
        # Exclude combinations already handled above
        exclude_terms = ['partner']
        
        has_gcc = any(term in query_lower for term in gcc_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual group Channel Champs
        if hasattr(self, 'df') and self.df is not None and 'Group Channel Champ' in self.df.columns:
            try:
                gcc_names = [str(name).lower() for name in self.df['Group Channel Champ'].dropna().unique() if pd.notna(name)]
                has_gcc = has_gcc or any(name in query_lower for name in gcc_names)
            except Exception as e:
                print(f"DEBUG: Error checking group Channel Champs: {e}")
        
        return has_gcc and not has_exclude

    def _is_group_business_manager_query(self, query_lower):
        """Check if this is a group business manager query"""
        gbm_terms = ['group business manager', 'gbm']
        # Exclude combinations already handled above
        exclude_terms = ['oem']
        
        has_gbm = any(term in query_lower for term in gbm_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual group business manager names
        if hasattr(self, 'df') and self.df is not None and 'Group Business Manager Name' in self.df.columns:
            try:
                gbm_names = [str(name).lower() for name in self.df['Group Business Manager Name'].dropna().unique() if pd.notna(name)]
                has_gbm = has_gbm or any(name in query_lower for name in gbm_names)
            except Exception as e:
                print(f"DEBUG: Error checking group business manager names: {e}")
        
        return has_gbm and not has_exclude

    def _is_channel_champ_query(self, query_lower):
        """Check if this is a channel champ query"""
        cc_terms = ['channel champ', 'cc']
        # Exclude combinations already handled above
        exclude_terms = ['group channel champ', 'partner']
        
        has_cc = any(term in query_lower for term in cc_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual Channel Champs
        if hasattr(self, 'df') and self.df is not None and 'Channel Champ' in self.df.columns:
            try:
                cc_names = [str(name).lower() for name in self.df['Channel Champ'].dropna().unique() if pd.notna(name)]
                has_cc = has_cc or any(name in query_lower for name in cc_names)
            except Exception as e:
                print(f"DEBUG: Error checking Channel Champs: {e}")
        
        return has_cc and not has_exclude

    def _is_business_head_query(self, query_lower):
        """Check if this is a business head query"""
        bh_terms = ['business head', 'bh']
        # Exclude combinations already handled above
        exclude_terms = ['oem']
        
        has_bh = any(term in query_lower for term in bh_terms)
        has_exclude = any(term in query_lower for term in exclude_terms)
        
        # Also check for actual business head names
        if hasattr(self, 'df') and self.df is not None and 'Business Head Name' in self.df.columns:
            try:
                bh_names = [str(name).lower() for name in self.df['Business Head Name'].dropna().unique() if pd.notna(name)]
                has_bh = has_bh or any(name in query_lower for name in bh_names)
            except Exception as e:
                print(f"DEBUG: Error checking business head names: {e}")
        
        return has_bh and not has_exclude
    
        # 1. Year Handler (Special Case)
    def handle_year_query(self, query):
        """Handle year-specific queries for revenue, GM, growth, and transaction count"""
        try:
            # Check if it's a year query
            if 'year' not in query.lower() and 'fy' not in query.lower():
                return None

            # Extract year from query
            year = None
            if 'fy' in query.lower():
                # Handle FY23 or FY2023 format
                year_part = query.lower().split('fy')[-1][:4]  # Get up to 4 characters after 'fy'
                if len(year_part) == 2:  # FY23 format
                    year = 2000 + int(year_part)
                elif len(year_part) == 4:  # FY2023 format
                    year = int(year_part)
            else:
                # Look for 4-digit year in query
                years_in_query = [int(word) for word in query.split() if word.isdigit() and len(word) == 4]
                if years_in_query:
                    year = years_in_query[0]

            # If no specific year mentioned, show all years
            if not year:
                return self.handle_all_years_query(query)

            # Check if year exists in data
            if year not in self.yearly_stats or year == 'comparisons':
                return f"❌ No data found for year: {year}"

            year_data = self.yearly_stats[year]

            # Determine what metric to return
            if 'revenue' in query.lower() or 'sales' in query.lower():
                return f"💰 Total Revenue for {year}: {format_in_crores(year_data['total_revenue'])}"
            elif 'margin' in query.lower() or 'gm' in query.lower():
                return f"💹 Total Gross Margin for {year}: {format_in_crores(year_data['total_gross_margin'])}"
            elif 'transaction' in query.lower() or 'count' in query.lower():
                return f"📊 Transaction Count for {year}: {year_data['total_transactions']:,}"
            elif 'growth' in query.lower():
                return self.handle_year_growth_query(year)
            else:
                # Return comprehensive year data if no specific metric requested
                result = f"📅 **Yearly Performance for {year}:**\n\n"
                result += f"💰 Total Revenue: {format_in_crores(year_data['total_revenue'])}\n"
                result += f"💹 Total Gross Margin: {format_in_crores(year_data['total_gross_margin'])}\n"
                result += f"📊 Transaction Count: {year_data['total_transactions']:,}\n"
                
                # Add growth if available
                if 'comparisons' in self.yearly_stats:
                    for comp_key, comp_data in self.yearly_stats['comparisons'].items():
                        if str(year) in comp_key and comp_key.endswith(str(year)):
                            prev_year = comp_key.split('_to_')[0]
                            result += f"\n📈 Growth from {prev_year}:\n"
                            result += f"   • Revenue: {comp_data['revenue_growth']:+.1f}%\n"
                            result += f"   • Gross Margin: {comp_data['margin_growth']:+.1f}%\n"
                            result += f"   • Transactions: {comp_data['transaction_growth']:+.1f}%\n"
                            break
                
                return result

        except Exception as e:
            return f"❌ Error processing year query: {e}"

    def handle_all_years_query(self, query):
        """Handle queries for all years data"""
        try:
            result = "📅 **Yearly Performance Summary**\n\n"
            
            # Sort years chronologically
            years = sorted([y for y in self.yearly_stats.keys() if y != 'comparisons'])
            
            for year in years:
                year_data = self.yearly_stats[year]
                result += f"**{year}:**\n"
                result += f"   • Revenue: {format_in_crores(year_data['total_revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(year_data['total_gross_margin'])}\n"
                result += f"   • Transactions: {year_data['total_transactions']:,}\n\n"
            
            # Add comparisons if available
            if 'comparisons' in self.yearly_stats and self.yearly_stats['comparisons']:
                result += "📈 **Year-over-Year Growth:**\n"
                for comp_key, comp_data in self.yearly_stats['comparisons'].items():
                    years = comp_key.split('_to_')
                    result += f"\n{years[0]} → {years[1]}:\n"
                    result += f"   • Revenue: {comp_data['revenue_growth']:+.1f}%\n"
                    result += f"   • Gross Margin: {comp_data['margin_growth']:+.1f}%\n"
                    result += f"   • Transactions: {comp_data['transaction_growth']:+.1f}%\n"
            
            return result
        except Exception as e:
            return f"❌ Error processing all years query: {e}"

    def handle_year_growth_query(self, year):
        """Handle specific growth queries for a year"""
        try:
            if 'comparisons' not in self.yearly_stats or not self.yearly_stats['comparisons']:
                return f"❌ No growth data available for {year}"
            
            # Find comparisons involving this year
            growth_data = None
            for comp_key, comp_data in self.yearly_stats['comparisons'].items():
                if str(year) == comp_key.split('_to_')[1]:  # This year is the "to" year
                    prev_year = comp_key.split('_to_')[0]
                    growth_data = {
                        'prev_year': prev_year,
                        'data': comp_data
                    }
                    break
            
            if not growth_data:
                return f"❌ No growth data available for {year} (might be earliest year)"
            
            result = f"📈 Growth from {growth_data['prev_year']} to {year}:\n\n"
            result += f"💰 Revenue Growth: {growth_data['data']['revenue_growth']:+.1f}%\n"
            result += f"   (Change: {format_in_crores(growth_data['data']['revenue_difference'])})\n"
            result += f"💹 Gross Margin Growth: {growth_data['data']['margin_growth']:+.1f}%\n"
            result += f"   (Change: {format_in_crores(growth_data['data']['margin_difference'])})\n"
            result += f"📊 Transaction Growth: {growth_data['data']['transaction_growth']:+.1f}%\n"
            result += f"   (Change: {growth_data['data']['transaction_difference']:+,.0f} transactions)\n"
            
            return result
        except Exception as e:
            return f"❌ Error processing growth query: {e}"

    def handle_region_query(self, query):
        """Handle Region specific queries with comprehensive multi-year analysis using HTML tables"""
        try:
            print(f"DEBUG: Region handler called with: {query}")
            
            # Check if Region column exists
            region_column = 'Region'
            if region_column not in self.df.columns:
                print("DEBUG: No Region column found")
                return "❌ Region data not available in this dataset"
            
            print(f"DEBUG: Available columns: {list(self.df.columns)}")
            
            # Extract region name from query - improved regex patterns
            query_lower = query.lower()
            region_match = None
            
            # Try multiple regex patterns for region extraction
            patterns = [
                r'region\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'region\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+region\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|performance).*?(?:for|of)\s+([^,\n]+?)(?:\s+region|$)'
            ]
            
            for pattern in patterns:
                region_match = re.search(pattern, query_lower)
                if region_match:
                    print(f"DEBUG: Region extracted with pattern: {pattern}")
                    break
            
            # If no regex match, try direct matching with available regions
            if not region_match:
                print("DEBUG: No regex match, trying direct region matching")
                available_regions = self.df[region_column].dropna().unique()
                matched_directly = None
                for region in available_regions:
                    if region.lower() in query_lower:
                        matched_directly = region
                        print(f"DEBUG: Direct match found: {region}")
                        break
                
                # Create a simple object with group method if we found a direct match
                if matched_directly:
                    class DirectMatch:
                        def __init__(self, value):
                            self.value = value
                        def group(self, index):
                            return self.value
                    region_match = DirectMatch(matched_directly)
            
            if not region_match:
                print("DEBUG: No region match found")
                available_regions = self.df[region_column].dropna().unique()
                return (f"❌ Please specify a Region name.\n"
                        f"Available: {', '.join(map(str, available_regions[:5]))}")
            
            requested_region = region_match.group(1).strip()
            print(f"DEBUG: Extracted region: '{requested_region}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_region = None
            available_regions = self.df[region_column].dropna().unique()
            
            print(f"DEBUG: Available regions: {list(available_regions)}")
            
            # Try exact match first
            for region in available_regions:
                if str(region).lower().strip() == requested_region.lower().strip():
                    matched_region = region
                    print(f"DEBUG: Exact match found: {matched_region}")
                    break
            
            # Try partial match if exact fails
            if not matched_region:
                for region in available_regions:
                    if requested_region.lower().strip() in str(region).lower().strip():
                        matched_region = region
                        print(f"DEBUG: Partial match found: {matched_region}")
                        break
            
            if not matched_region:
                print(f"DEBUG: No match found for '{requested_region}'")
                return (f"❌ Region '{requested_region}' not found.\n"
                        f"Available: {', '.join(map(str, available_regions[:5]))}")
            
            # Get all available years for this region
            region_data = self.df[self.df[region_column] == matched_region]
            available_years = sorted(region_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for Region {matched_region}"
            
            print(f"DEBUG: Available years for {matched_region}: {available_years}")
            
            # Create a unique identifier for this region to avoid ID conflicts
            region_id = matched_region.lower().replace(' ', '_').replace('-', '_')
            
            # Get latest year as default
            latest_year = max(available_years)
            
            # Build comprehensive output with HTML tables and dropdown selectors
            output_text = f"""## PERFORMANCE FOR {matched_region.upper()} REGION

    <div style="margin-bottom: 20px; padding: 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: center;">
            <!-- Year Filter -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <label for="yearSelector_{region_id}" style="font-weight: bold; margin-bottom: 8px; font-size: 14px; color: #495057;">Select Year:</label>
                <select id="yearSelector_{region_id}" onchange="updateYearDisplay_{region_id}()" style="padding: 10px 15px; border: 1px solid #ced4da; border-radius: 6px; background-color: white; font-size: 14px; min-width: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">"""

            # Add year options
            for year in reversed(available_years):  # Latest first
                year_str = f"{year}-{str(year+1)[2:]}"
                selected = "selected" if year == latest_year else ""
                output_text += f'<option value="{year}" {selected}>{year_str}</option>'

            output_text += f"""
                </select>
            </div>
            
            <!-- Top N Filter -->
            <div style="display: flex; flex-direction: column; align-items: center;">
                <label for="topNSelector_{region_id}" style="font-weight: bold; margin-bottom: 8px; font-size: 14px; color: #495057;">Select Top N:</label>
                <select id="topNSelector_{region_id}" onchange="updateTopNDisplay_{region_id}()" style="padding: 10px 15px; border: 1px solid #ced4da; border-radius: 6px; background-color: white; font-size: 14px; min-width: 120px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <option value="5" selected>Top 5</option>
                    <option value="10">Top 10</option>
                    <option value="15">Top 15</option>
                    <option value="20">Top 20</option>
                    <option value="all">Show All</option>
                </select>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <span style="font-size: 12px; color: #6c757d; font-style: italic;">
                Year filter applies to OEMs, Partners, and End Customers tables. Top N filter applies to dynamic tables only.
            </span>
        </div>
    </div>

    <script>
    function updateYearDisplay_{region_id}() {{
        const yearSelector = document.getElementById('yearSelector_{region_id}');
        const selectedYear = yearSelector.value;
        
        // Hide all year-specific sections first
        const allYearSections = document.querySelectorAll('[data-year-section-{region_id}]');
        allYearSections.forEach(section => {{
            section.style.display = 'none';
        }});
        
        // Show selected year sections
        const selectedSections = document.querySelectorAll(`[data-year-section-{region_id}="${{selectedYear}}"]`);
        selectedSections.forEach(section => {{
            section.style.display = 'block';
        }});
        
        // Update year display in yearly summary if it exists
        const yearlyDisplay = document.getElementById('yearlyDisplay_{region_id}');
        if (yearlyDisplay) {{
            const yearStr = selectedYear + '-' + (parseInt(selectedYear) + 1).toString().slice(-2);
            yearlyDisplay.textContent = `Performance Summary - ${{yearStr}}`;
        }}
    }}

    function updateTopNDisplay_{region_id}() {{
        const selector = document.getElementById('topNSelector_{region_id}');
        const selectedValue = selector.value;
        
        // Get all tables with class 'dynamic-top-n-{region_id}'
        const tables = document.querySelectorAll('table.dynamic-top-n-{region_id}');
        
        tables.forEach(table => {{
            const tbody = table.querySelector('tbody');
            const rows = tbody.querySelectorAll('tr');
            
            if (selectedValue === 'all') {{
                // Show all rows
                rows.forEach(row => row.style.display = '');
            }} else {{
                const topN = parseInt(selectedValue);
                // Show/hide rows based on selection
                rows.forEach((row, index) => {{
                    if (index < topN) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }});
            }}
            
            // Update table titles
            const titleElement = table.closest('div').querySelector('.table-title-dynamic-{region_id}');
            if (titleElement) {{
                const originalTitle = titleElement.getAttribute('data-original-title');
                if (originalTitle) {{
                    if (selectedValue === 'all') {{
                        titleElement.textContent = originalTitle.replace(/TOP \\d+/, 'ALL');
                    }} else {{
                        titleElement.textContent = originalTitle.replace(/TOP \\d+|ALL/, `TOP ${{selectedValue}}`);
                    }}
                }}
            }}
        }});
    }}

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {{
        // Set default displays
        updateYearDisplay_{region_id}();
        updateTopNDisplay_{region_id}();
    }});

    // Also run after a short delay to ensure all content is loaded
    setTimeout(function() {{
        updateYearDisplay_{region_id}();
        updateTopNDisplay_{region_id}();
    }}, 100);
    </script>

    """
            
            # Year-wise performance summary table (always show all years for context)
            yearly_summary_data = []
            for year in available_years:
                year_data = region_data[region_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = region_data[region_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str
                })
            
            # Create yearly summary table (always visible)
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_html_table(
                    yearly_df,
                    table_id=f"{region_id}_yearly_summary",
                    title=f"{matched_region} Region - All Years Performance Summary",
                    highlight_total=False
                )
                output_text += yearly_table_html + "\n\n"
            
            # Helper function to get analysis tables for each category (modified for year filtering)
            def get_yearly_analysis_table(group_column, title, show_all=False):
                if group_column not in region_data.columns:
                    return f"### {title.upper()}\n\n❌ Column '{group_column}' not found in data\n\n"
                
                section_text = f"### {'ALL' if show_all else 'TOP 5'} {title.upper()}\n\n"
                
                for year in available_years:
                    year_data = region_data[region_data['Year_Start'] == year]
                    prev_year_data = region_data[region_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty values
                    year_filtered = year_data[year_data[group_column].notna() & (year_data[group_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats - Get ALL records for dynamic tables
                    current_stats = year_filtered.groupby(group_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and group_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[group_column].notna() & (prev_year_data[group_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(group_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=group_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        name = str(row[group_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        table_data.append({
                            'Name': name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        
                        # Create DataFrame and generate HTML table with year filtering
                        category_df = pd.DataFrame(table_data)
                        
                        # Determine if this year should be visible by default (latest year)
                        is_default_visible = year == latest_year
                        year_section_style = '' if is_default_visible else 'display: none;'
                        
                        # Add year-specific wrapper div
                        section_text += f'<div data-year-section-{region_id}="{year}" style="{year_section_style}">\n'
                        section_text += f"**{year_str}:**\n\n"
                        
                        # Generate HTML table
                        if not show_all:  # Dynamic tables (OEMs, Partners, End Customers)
                            table_html = generate_dynamic_html_table(
                                category_df,
                                table_id=f"{region_id}_{title.lower().replace(' ', '_')}_{year}",
                                title=f"TOP 5 {title} - {year_str}",
                                region_id=region_id
                            )
                        else:  # Static tables (Vertical Accounts and Channels)
                            table_html = self._generate_html_table(
                                category_df,
                                table_id=f"{region_id}_{title.lower().replace(' ', '_')}_{year}",
                                title=f"{title} - {year_str}",
                                highlight_total=False
                            )
                        
                        section_text += table_html + "\n"
                        section_text += "</div>\n\n"
                
                return section_text
            
            # Custom HTML table generator for dynamic tables
            def generate_dynamic_html_table(df, table_id, title, region_id):
                """Generate HTML table with dynamic top N functionality"""
                
                html = f"""
    <div style="margin: 20px 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; font-weight: bold; text-align: center;">
            <span class="table-title-dynamic-{region_id}" data-original-title="{title}">{title}</span>
        </div>
        <div style="overflow-x: auto;">
            <table class="dynamic-top-n-{region_id}" style="width: 100%; border-collapse: collapse; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <thead style="background-color: #f8f9fa;">
                    <tr>
    """
                
                # Add headers
                for col in df.columns:
                    html += f'<th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6; font-weight: 600; color: #495057;">{col}</th>'
                
                html += """
                    </tr>
                </thead>
                <tbody>
    """
                
                # Add data rows with initial display logic for Top 5
                for idx, row in df.iterrows():
                    # Hide rows beyond index 4 (Top 5) by default
                    row_style = '' if idx < 5 else 'display: none;'
                    html += f'<tr style="{row_style}">'
                    
                    for col in df.columns:
                        cell_value = str(row[col])
                        cell_style = "padding: 10px 8px; border-bottom: 1px solid #dee2e6;"
                        
                        # Add color coding for growth values
                        if 'Growth' in col and cell_value not in ['N/A', 'New']:
                            if cell_value.startswith('+'):
                                cell_style += " color: #28a745; font-weight: 500;"  # Green for positive
                            elif cell_value.startswith('-'):
                                cell_style += " color: #dc3545; font-weight: 500;"  # Red for negative
                        
                        html += f'<td style="{cell_style}">{cell_value}</td>'
                    
                    html += '</tr>'
                
                html += """
                </tbody>
            </table>
        </div>
    </div>
    """
                
                return html
            
            # Find column mappings with multiple patterns
            def find_column_with_patterns(patterns, available_cols):
                """Find column using multiple pattern matching strategies"""
                for pattern in patterns:
                    # Exact match (case insensitive)
                    for col in available_cols:
                        if pattern.lower() == col.lower():
                            return col
                    
                    # Contains match
                    for col in available_cols:
                        if pattern.lower() in col.lower() or col.lower() in pattern.lower():
                            return col
                
                return None
            
            # Get available columns and find mappings
            available_columns = list(region_data.columns)
            
            # Enhanced column mapping
            oem_column = find_column_with_patterns(['OEM', 'Vendor', 'Manufacturer', 'Brand'], available_columns)
            partner_column = find_column_with_patterns(['Partner', 'Reseller', 'Distributor', 'Channel Partner', 'System Integrator'], available_columns)
            end_customer_column = find_column_with_patterns(['End Customer Name', 'End Customer', 'Customer Name', 'Customer', 'Client', 'End Customer (Biz)'], available_columns)
            vertical_column = find_column_with_patterns(['Vertical Account', 'Vertical', 'Vertical Champ', 'Industry'], available_columns)
            channel_column = find_column_with_patterns(['Channel', 'Sales Channel', 'Channel Type'], available_columns)
            
            # Add the analyses with HTML tables (with year filtering for dynamic tables)
            if oem_column:
                output_text += get_yearly_analysis_table(oem_column, 'OEMs', show_all=False)
            else:
                output_text += "### TOP 5 OEMS\n❌ OEM column not found in data\n\n"
                
            if partner_column:
                output_text += get_yearly_analysis_table(partner_column, 'Partners', show_all=False)
            else:
                output_text += "### TOP 5 PARTNERS\n❌ Partner column not found in data\n\n"
                
            if end_customer_column:
                output_text += get_yearly_analysis_table(end_customer_column, 'End Customers', show_all=False)
            else:
                output_text += "### TOP 5 END CUSTOMERS\n❌ End Customer column not found in data\n\n"
                
            # Note: Vertical and Channel tables remain static (show all years) as they use show_all=True
            if vertical_column:
                output_text += get_yearly_analysis_table(vertical_column, 'Vertical Accounts', show_all=True)
            else:
                output_text += "### ALL VERTICAL ACCOUNTS\n❌ Vertical Account column not found in data\n\n"
                
            if channel_column:
                output_text += get_yearly_analysis_table(channel_column, 'Channels', show_all=True)
            else:
                output_text += "### ALL CHANNELS\n❌ Channel column not found in data\n\n"
            
            print(f"DEBUG: Generated comprehensive HTML table report with year filtering for {matched_region}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing Region query: {str(e)}"

    def handle_vertical_champ_query(self, query):
            """Handle Vertical Champ specific queries"""
            try:
                print(f"DEBUG: Vertical Champ handler called with: {query}")
                
                # Determine the correct column name - check all possible variations
                champ_column = None
                possible_columns = [
                    'Vertical Champ', 'Vertical Champ Name', 
                    'VerticalChamp', 'Vertical_Champ'
                ]
                
                print(f"DEBUG: Available columns: {list(self.df.columns)}")
                
                for col in possible_columns:
                    if col in self.df.columns:
                        champ_column = col
                        print(f"DEBUG: Found column: {champ_column}")
                        break
                            
                if not champ_column:
                    print("DEBUG: No Vertical Champ column found")
                    return "❌ Vertical Champ data not available in this dataset"
                
                # Extract name from query - improved regex patterns
                query_lower = query.lower()
                name_match = None
                
                # Try multiple regex patterns for name extraction
                patterns = [
                    r'vertical\s+champ\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                    r'vertical\s+champ\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                    r'of\s+vertical\s+champ\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)'
                ]
                
                for pattern in patterns:
                    name_match = re.search(pattern, query_lower)
                    if name_match:
                        print(f"DEBUG: Name extracted with pattern: {pattern}")
                        break
                
                if not name_match:
                    print("DEBUG: No name match found")
                    available_champs = self.df[champ_column].dropna().unique()
                    return (f"❌ Please specify a Vertical Champ name.\n"
                            f"Available: {', '.join(map(str, available_champs[:5]))}")
                
                requested_name = name_match.group(1).strip()
                print(f"DEBUG: Extracted name: '{requested_name}'")
                
                # Find exact match (case insensitive) - improved matching
                matched_name = None
                available_names = self.df[champ_column].dropna().unique()
                
                print(f"DEBUG: Available names: {list(available_names)}")
                
                # Try exact match first
                for name in available_names:
                    if str(name).lower().strip() == requested_name.lower().strip():
                        matched_name = name
                        print(f"DEBUG: Exact match found: {matched_name}")
                        break
                
                # Try partial match if exact fails
                if not matched_name:
                    for name in available_names:
                        if requested_name.lower().strip() in str(name).lower().strip():
                            matched_name = name
                            print(f"DEBUG: Partial match found: {matched_name}")
                            break
                
                if not matched_name:
                    print(f"DEBUG: No match found for '{requested_name}'")
                    return (f"❌ Vertical Champ '{requested_name}' not found.\n"
                            f"Available: {', '.join(map(str, available_names[:5]))}")
                
                # Extract year if specified
                year = None
                year_match = re.search(r'(?:year\s+)?(?:fy\s*)?(?:20)?(\d{2})', query_lower)
                if year_match:
                    year_num = int(year_match.group(1))
                    year = 2000 + year_num if year_num > 50 else 2000 + year_num
                    print(f"DEBUG: Extracted year: {year}")
                
                # Get champ data
                print(f"DEBUG: Filtering data for {matched_name}")
                champ_data = self.df[self.df[champ_column] == matched_name]
                print(f"DEBUG: Found {len(champ_data)} total records for {matched_name}")
                
                if year:
                    champ_data = champ_data[champ_data['Year_Start'] == year]
                    print(f"DEBUG: Found {len(champ_data)} records for {matched_name} in year {year}")
                
                if len(champ_data) == 0:
                    return f"ℹ️ No data found for Vertical Champ {matched_name}" + (f" in {year}" if year else "")
                
                # Calculate metrics
                total_revenue = champ_data['TL Base Value'].sum()
                total_margin = champ_data['Gross Margin Value'].sum()
                transaction_count = len(champ_data)
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                
                print(f"DEBUG: Calculated metrics - Revenue: {total_revenue}, Margin: {total_margin}, Count: {transaction_count}")
                
                # Format response - SAME AS CHANNEL QUERY
                if 'revenue' in query.lower():
                    result = f"💰 Vertical Champ: {matched_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
                elif 'margin' in query.lower():
                    result = f"💹 Vertical Champ: {matched_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
                elif 'transaction' in query.lower() or 'count' in query.lower():
                    result = f"📊 Vertical Champ: {matched_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {transaction_count:,}"
                else:
                    result = (f"📊 Vertical Champ: {matched_name} Performance (FY{str(year)[2:] if year else 'All Time'}):\n"
                        f"   • Revenue: {format_in_crores(total_revenue)}\n"
                        f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)\n"
                        f"   • Transactions: {transaction_count:,}")
                
                print(f"DEBUG: Final result: {result}")
                return result
                    
            except Exception as e:
                print(f"DEBUG: Exception occurred: {str(e)}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                return f"❌ Error processing Vertical Champ query: {str(e)}"

    def handle_business_manager_query(self, query):
        """Handle all Business Manager-related queries (revenue, margin, transactions, growth)"""
        try:
            # Extract year if specified (handles both FY22 and 2022 formats)
            year = None
            year_match = re.search(r'(?:in year|in|for|during|fy)\s*(20)?(\d{2})', query.lower())
            if year_match:
                year = 2000 + int(year_match.group(2))
            
            # Determine which column to use (prefer 'Business Manager Name' over 'Business Manager')
            manager_column = None
            for col in ['Business Manager Name', 'Business Manager']:
                if col in self.df.columns:
                    manager_column = col
                    break
            
            if not manager_column:
                return "❌ No Business Manager data available in this dataset"
            
            # Get available managers first for better matching
            available_managers = self.df[manager_column].dropna().unique()
            
            # Improved Business Manager name extraction with multiple patterns
            manager_name = None
            requested_manager = None
            
            # Pattern 1: Direct manager name matching (most reliable)
            for manager in available_managers:
                if str(manager).lower() in query.lower():
                    manager_name = manager
                    requested_manager = str(manager).lower()
                    break
            
            if not manager_name:
                # Pattern 2: "business manager [name]" - stop at common keywords
                manager_match = re.search(
                    r'(?:business\s+manager\s+name|business\s+manager)\s+([^,]+?)(?:\s+(?:in|for|during|revenue|margin|transaction|count|growth|performance|year|\d{4})|$)',
                    query.lower()
                )
                if manager_match:
                    requested_manager = manager_match.group(1).strip()
                else:
                    # Pattern 3: "for/of [name] business manager"
                    manager_match = re.search(
                        r'(?:for|of|by)\s+([^,]+?)(?:\s+(?:business\s+manager|revenue|margin|transaction|count|growth|performance|year|\d{4})|$)',
                        query.lower()
                    )
                    if manager_match:
                        requested_manager = manager_match.group(1).strip()
            
            if not requested_manager and not manager_name:
                return "❌ Please specify a valid Business Manager name"
            
            # Find exact Business Manager name match if not already found
            if not manager_name and requested_manager:
                best_match_score = 0
                requested_lower = requested_manager.lower()
                
                # Try exact match first
                for manager in available_managers:
                    manager_str = str(manager).lower()
                    if manager_str == requested_lower:
                        manager_name = manager
                        break
                    elif requested_lower in manager_str:
                        match_score = len(requested_lower) / len(manager_str)
                        if match_score > best_match_score:
                            best_match_score = match_score
                            manager_name = manager
            
            if not manager_name:
                available_managers_list = [str(manager) for manager in available_managers if str(manager) != '-'][:10]
                return f"❌ Business Manager '{requested_manager}' not found. Available managers: {', '.join(available_managers_list)}"
            
            # Get Business Manager data with exact match
            manager_data = self.df[self.df[manager_column].str.lower() == str(manager_name).lower()]
            if year:
                manager_data = manager_data[manager_data['Year_Start'] == year]
            
            if len(manager_data) == 0:
                return f"❌ No data found for Business Manager {manager_name}" + (f" in {year}" if year else "")
            
            # Calculate comprehensive metrics
            total_revenue = manager_data['TL Base Value'].sum() if 'TL Base Value' in manager_data.columns else 0
            total_margin = manager_data['Gross Margin Value'].sum() if 'Gross Margin Value' in manager_data.columns else 0
            transaction_count = len(manager_data)
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            # Determine what metric to return based on query content
            query_lower = query.lower()
            
            if 'revenue' in query_lower and total_revenue > 0:
                return f"💰 Business Manager: {manager_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
            
            elif 'margin' in query_lower and total_margin > 0:
                return f"💹 Business Manager: {manager_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
            
            elif 'transaction' in query_lower or 'count' in query_lower:
                return f"📊 Business Manager: {manager_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {transaction_count:,}"
            
            elif 'growth' in query_lower and year:
                # Calculate growth from previous year (inline)
                prev_year = year - 1
                
                # Get data for previous year
                prev_data = self.df[
                    (self.df[manager_column].str.lower() == str(manager_name).lower()) & 
                    (self.df['Year_Start'] == prev_year)
                ]
                
                if len(prev_data) == 0:
                    return f"❌ Cannot calculate growth - no data for {prev_year}"
                
                # Calculate metrics for both years
                prev_revenue = prev_data['TL Base Value'].sum() if 'TL Base Value' in prev_data.columns else 0
                prev_margin = prev_data['Gross Margin Value'].sum() if 'Gross Margin Value' in prev_data.columns else 0
                prev_count = len(prev_data)
                
                # Calculate growth percentages
                rev_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                return (f"📈 Business Manager: {manager_name} Growth (FY{str(prev_year)[2:]}→FY{str(year)[2:]}):\n"
                    f"   • Revenue Growth: {rev_growth:+.1f}%\n"
                    f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    f"   • Transaction Growth: {count_growth:+.1f}%")
            
            else:
                # Default comprehensive response
                year_str = f" (FY{str(year)[2:]})" if year else ""
                response_parts = [f"📊 Business Manager: {manager_name} Performance{year_str}:"]
                
                if total_revenue > 0:
                    response_parts.append(f"   • Revenue: {format_in_crores(total_revenue)}")
                if total_margin > 0:
                    response_parts.append(f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)")
                response_parts.append(f"   • Transactions: {transaction_count:,}")
                
                return "\n".join(response_parts)
        
        except Exception as e:
            return f"❌ Error processing Business Manager query: {str(e)}"

    def handle_group_business_manager_query(self, query):
        """Handle all Group Business Manager-related queries"""
        try:
            # First verify the column exists
            if 'Group Business Manager Name' not in self.df.columns:
                return "❌ Group Business Manager data not available in this dataset"
                
            # Extract Group Business Manager name (case-insensitive, exact match)
            manager_name = None
            query_lower = query.lower()
            
            # Look for exact name match in the column
            for manager in self.df['Group Business Manager Name'].dropna().unique():
                if str(manager).lower() in query_lower:
                    manager_name = manager
                    break
            
            if not manager_name:
                available_managers = self.df['Group Business Manager Name'].dropna().unique()[:5]
                return (f"❌ Please specify a valid Group Business Manager name. "
                    f"Available: {', '.join(map(str, available_managers))}")

            # Extract year if specified
            year = None
            year_match = re.search(r'(?:20)?(\d{2})', query)
            if year_match:
                year = 2000 + int(year_match.group(1))

            # Get manager data - ensure we're using the correct column
            manager_data = self.df[
                (self.df['Group Business Manager Name'].str.lower() == manager_name.lower())
            ]
            
            if year:
                manager_data = manager_data[manager_data['Year_Start'] == year]
            
            if len(manager_data) == 0:
                return f"❌ No data found for Group Business Manager {manager_name}" + (f" in {year}" if year else "")

            # Calculate metrics
            total_revenue = manager_data['TL Base Value'].sum()
            total_margin = manager_data['Gross Margin Value'].sum()
            transaction_count = len(manager_data)
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

            # Determine what metric to return based on query keywords
            if 'revenue' in query_lower:
                return f"💰 Group Business Manager: {manager_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
            
            elif 'margin' in query_lower:
                return f"💹 Group Business Manager: {manager_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
            
            elif 'transaction' in query_lower or 'count' in query_lower:
                return f"📊 Group Business Manager: {manager_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {transaction_count:,}"
            
            elif 'growth' in query_lower and year:
                # Calculate growth from previous year
                prev_year = year - 1
                prev_data = self.df[
                    (self.df['Group Business Manager Name'].str.lower() == manager_name.lower()) & 
                    (self.df['Year_Start'] == prev_year)
                ]
                
                if len(prev_data) == 0:
                    return f"❌ Cannot calculate growth - no data for {prev_year}"
                
                prev_revenue = prev_data['TL Base Value'].sum()
                prev_margin = prev_data['Gross Margin Value'].sum()
                prev_count = len(prev_data)
                
                rev_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                margin_growth = ((total_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                count_growth = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                return (f"📈 Group Business Manager: {manager_name} Growth (FY{prev_year}→FY{year}):\n"
                    f"   • Revenue Growth: {rev_growth:+.1f}%\n"
                    f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    f"   • Transaction Growth: {count_growth:+.1f}%")
            
            else:
                # Default comprehensive response
                year_str = f" (FY{str(year)[2:]})" if year else ""
                return (f"📊 Group Business Manager: {manager_name} Performance{year_str}:\n"
                    f"   • Revenue: {format_in_crores(total_revenue)}\n"
                    f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)\n"
                    f"   • Transactions: {transaction_count:,}")

        except Exception as e:
            return f"❌ Error processing Group Business Manager query: {str(e)}"

    def handle_group_channel_champ_query(self, query):
        """Handle Group Channel Champ specific queries"""
        try:
            print(f"DEBUG: Group Channel Champ handler called with: {query}")
            
            # Determine the correct column name - check all possible variations
            champ_column = None
            possible_columns = [
                'Group Channel Champ', 'Group Channel Champ', 
                'Channel Champ', 'Channel Champ',
                'GroupChannelChamp', 'Group_Channel_Champ'
            ]
            
            print(f"DEBUG: Available columns: {list(self.df.columns)}")
            
            for col in possible_columns:
                if col in self.df.columns:
                    champ_column = col
                    print(f"DEBUG: Found column: {champ_column}")
                    break
                        
            if not champ_column:
                print("DEBUG: No Group Channel Champ column found")
                return "❌ Group Channel Champ data not available in this dataset"
            
            # Extract name from query - improved regex patterns
            query_lower = query.lower()
            name_match = None
            
            # Try multiple regex patterns for name extraction
            patterns = [
                r'group\s+channel\s+champ\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'group\s+channel\s+champ\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+group\s+channel\s+champ\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)'
            ]
            
            for pattern in patterns:
                name_match = re.search(pattern, query_lower)
                if name_match:
                    print(f"DEBUG: Name extracted with pattern: {pattern}")
                    break
            
            if not name_match:
                print("DEBUG: No name match found")
                available_champs = self.df[champ_column].dropna().unique()
                return (f"❌ Please specify a Group Channel Champ.\n"
                        f"Available: {', '.join(map(str, available_champs[:5]))}")
            
            requested_name = name_match.group(1).strip()
            print(f"DEBUG: Extracted name: '{requested_name}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_name = None
            available_names = self.df[champ_column].dropna().unique()
            
            print(f"DEBUG: Available names: {list(available_names)}")
            
            # Try exact match first
            for name in available_names:
                if str(name).lower().strip() == requested_name.lower().strip():
                    matched_name = name
                    print(f"DEBUG: Exact match found: {matched_name}")
                    break
            
            # Try partial match if exact fails
            if not matched_name:
                for name in available_names:
                    if requested_name.lower().strip() in str(name).lower().strip():
                        matched_name = name
                        print(f"DEBUG: Partial match found: {matched_name}")
                        break
            
            if not matched_name:
                print(f"DEBUG: No match found for '{requested_name}'")
                return (f"❌ Group Channel Champ '{requested_name}' not found.\n"
                        f"Available: {', '.join(map(str, available_names[:5]))}")
            
            # Extract year if specified
            year = None
            year_match = re.search(r'(?:year\s+)?(?:fy\s*)?(?:20)?(\d{2})', query_lower)
            if year_match:
                year_num = int(year_match.group(1))
                year = 2000 + year_num if year_num > 50 else 2000 + year_num
                print(f"DEBUG: Extracted year: {year}")
            
            # Get champ data
            print(f"DEBUG: Filtering data for {matched_name}")
            champ_data = self.df[self.df[champ_column] == matched_name]
            print(f"DEBUG: Found {len(champ_data)} total records for {matched_name}")
            
            if year:
                champ_data = champ_data[champ_data['Year_Start'] == year]
                print(f"DEBUG: Found {len(champ_data)} records for {matched_name} in year {year}")
            
            if len(champ_data) == 0:
                return f"ℹ️ No data found for Group Channel Champ {matched_name}" + (f" in {year}" if year else "")
            
            # Calculate metrics
            total_revenue = champ_data['TL Base Value'].sum()
            total_margin = champ_data['Gross Margin Value'].sum()
            transaction_count = len(champ_data)
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            print(f"DEBUG: Calculated metrics - Revenue: {total_revenue}, Margin: {total_margin}, Count: {transaction_count}")
            
            # Format response - SAME AS CHANNEL QUERY
            if 'revenue' in query.lower():
                result = f"💰 Group Channel Champ: {matched_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
            elif 'margin' in query.lower():
                result = f"💹 Group Channel Champ: {matched_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
            elif 'transaction' in query.lower() or 'count' in query.lower():
                result = f"📊 Group Channel Champ: {matched_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {transaction_count:,}"
            else:
                result = (f"📊 Group Channel Champ: {matched_name} Performance (FY{str(year)[2:] if year else 'All Time'}):\n"
                    f"   • Revenue: {format_in_crores(total_revenue)}\n"
                    f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)\n"
                    f"   • Transactions: {transaction_count:,}")
            
            print(f"DEBUG: Final result: {result}")
            return result
                
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing Group Channel Champ query: {str(e)}"


    def handle_channel_champ_query(self, query):
        """Handle all Channel Champ-related queries including revenue, margin, transactions, and growth analysis"""
        try:
            # Define constants at the top - using final annotation to help static analysis
            CHAMP_COLUMN: str = "Channel Champ"
            REVENUE_COL: str = "TL Base Value"
            MARGIN_COL: str = "Gross Margin Value"
            
            # 1. Check if required data exists
            if CHAMP_COLUMN not in self.df.columns:
                return "❌ Channel Champ data not available in this dataset"
            
            # 2. Enhanced name extraction with multiple patterns
            name_match = None
            query_lower = query.lower()
            
            # Pattern 1: "channel champ [name] in/for/during/year/fy"
            name_match = re.search(
                r'channel champ\s+(.+?)(?:\s+(?:in|for|during|year|fy|20\d{2}|\d{4}))', 
                query_lower
            )
            
            if not name_match:
                # Pattern 2: "channel champ [name]" at end of sentence or followed by specific words
                name_match = re.search(
                    r'channel champ\s+(.+?)(?:\s+(?:revenue|margin|transaction|performance|data)|$)', 
                    query_lower
                )
            
            if not name_match:
                # Pattern 3: Simple "channel champ [name]" extraction
                name_match = re.search(r'channel champ\s+(.+)', query_lower)
            
            # Pattern 4: Try to find any known Channel Champ in the query
            found_champ_name = None
            if not name_match:
                available_champs = [c for c in self.df[CHAMP_COLUMN].dropna().unique() if str(c) != '-']
                for champ_name in available_champs:
                    if str(champ_name).lower() in query_lower:
                        found_champ_name = str(champ_name)
                        break
            
            if not name_match and not found_champ_name:
                available_champs = [c for c in self.df[CHAMP_COLUMN].dropna().unique() if str(c) != '-'][:5]
                return f"❌ Please specify a Channel Champ. Available: {', '.join(map(str, available_champs))}"
            
            # Extract and clean the name
            if found_champ_name:
                requested_name = found_champ_name.strip().title()
            elif name_match:
                requested_name = name_match.group(1).strip().title()
            else:
                # This shouldn't happen due to earlier checks, but just in case
                available_champs = [c for c in self.df[CHAMP_COLUMN].dropna().unique() if str(c) != '-'][:5]
                return f"❌ Please specify a Channel Champ. Available: {', '.join(map(str, available_champs))}"
            
            # 3. Find exact match in the data (case insensitive)
            matched_name = None
            for name in self.df[CHAMP_COLUMN].dropna().unique():
                if str(name).lower() == requested_name.lower():
                    matched_name = name
                    break
            
            if not matched_name:
                available_champs = [c for c in self.df[CHAMP_COLUMN].dropna().unique() if str(c) != '-'][:5]
                return f"❌ Channel Champ: '{requested_name}' not found. Available: {', '.join(map(str, available_champs))}"

            # 4. Enhanced year extraction
            year = None
            # Try to extract 4-digit year first
            year_match = re.search(r'(20\d{2})', query)
            if not year_match:
                # Try 2-digit year
                year_match = re.search(r'(?:year|fy)\s*(\d{2})', query.lower())
                if year_match:
                    year_val = int(year_match.group(1))
                    year = 2000 + year_val if year_val > 50 else 2000 + year_val
            else:
                year = int(year_match.group(1))
            
            # 5. Get champ data
            champ_data = self.df[self.df[CHAMP_COLUMN].str.lower() == str(matched_name).lower()]
            if year:
                champ_data = champ_data[champ_data['Year_Start'] == year]
            
            if len(champ_data) == 0:
                year_info = f" in {year}" if year else ""
                available_years = sorted(self.df[self.df[CHAMP_COLUMN].str.lower() == str(matched_name).lower()]['Year_Start'].unique()) if not year else []
                year_msg = f" Available years: {available_years}" if available_years else ""
                return f"ℹ️ No data found for Channel Champ {matched_name}{year_info}.{year_msg}"
            
            # 6. Calculate metrics
            total_revenue = champ_data[REVENUE_COL].sum()
            total_margin = champ_data[MARGIN_COL].sum()
            transaction_count = len(champ_data)
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            # 7. Format response based on query focus
            if 'margin' in query.lower():
                return f"💹 Channel Champ: {matched_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
            elif 'revenue' in query.lower():
                return f"💰 Channel Champ: {matched_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
            elif 'transaction' in query.lower():
                return f"📊 Channel Champ: {matched_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {transaction_count:,}"
            else:
                # Default comprehensive response
                return (f"📊 Channel Champ: {matched_name} Performance (FY{str(year)[2:] if year else 'All Time'}):\n"
                    f"   • Revenue: {format_in_crores(total_revenue)}\n"
                    f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)\n"
                    f"   • Transactions: {transaction_count:,}")

        except Exception as e:
            # Enhanced error handling with debug info
            champ_col = "Channel Champ"
            available = []
            try:
                available = [c for c in self.df[champ_col].dropna().unique() if str(c) != '-'][:5]
            except:
                pass
            
            return (f"❌ Error processing Channel Champ query: {str(e)}\n"
                    f"Available Channel Champs: {', '.join(map(str, available)) if available else 'None found'}")

    def handle_business_head_query(self, query):
        """Handle all Business Head-related queries (revenue, margin, transactions, growth)"""
        # Define the expected column name
        BUSINESS_HEAD_COLUMN = "Business Head Name"
        
        try:
            # First check if the column exists in the DataFrame
            if BUSINESS_HEAD_COLUMN not in self.df.columns:
                return "❌ Business Head data not available in this dataset"
            
            # Normalize the query for processing
            query_lower = query.lower()
            
            # Multiple approaches to extract business head name
            bh_name = None
            
            # Method 1: Improved regex for various query formats
            name_match = re.search(
                r'business head(?: name)?\s+(.+?)(?:\s+(?:in|for|during|year|\d{4})|$)', 
                query, 
                re.IGNORECASE
            )
            
            if name_match:
                head_name = name_match.group(1).strip()
                
                # Find exact match first (case-insensitive)
                exact_match = None
                possible_matches = []
                
                for name in self.df[BUSINESS_HEAD_COLUMN].dropna().unique():
                    name_str = str(name).strip()  # Remove any extra whitespace
                    # Exact match (case insensitive)
                    if head_name.lower() == name_str.lower():
                        exact_match = name_str
                        break
                    # Partial match for fallback
                    if head_name.lower() in name_str.lower():
                        possible_matches.append(name_str)
                
                # Handle matches
                if exact_match:
                    bh_name = exact_match
                elif possible_matches:
                    if len(possible_matches) == 1:
                        bh_name = possible_matches[0]
                    else:
                        return (f"❌ Multiple possible matches for '{head_name}':\n"
                                f"{', '.join(possible_matches[:5])}\n"
                                f"Please specify the exact name.")
            
            # Method 2: Fallback to direct name search in query
            if not bh_name:
                for bh in self.df[BUSINESS_HEAD_COLUMN].dropna().unique():
                    if str(bh).lower() in query_lower:
                        bh_name = str(bh).strip()
                        break
            
            # If still no name found, return error with available options
            if not bh_name:
                available_heads = self.df[BUSINESS_HEAD_COLUMN].dropna().unique()[:5]
                return (f"❌ Could not identify business head name in query.\n"
                        f"Available: {', '.join(map(str, available_heads))}")

            # Enhanced year extraction - handles fiscal years like "2022-23" and "FY23"
            year = None
            year_patterns = [
                r'in\s+year\s+(\d{4}-\d{2})',  # Matches "2022-23"
                r'in\s+year\s+(fy\d{2})',      # Matches "FY23"
                r'in\s+(\d{4}-\d{2})',         # Matches "2022-23" without "year"
                r'in\s+(fy\d{2})',             # Matches "FY23" without "year"
                r'year\s+(\d{4}-\d{2})',       # Matches "year 2022-23"
                r'year\s+(fy\d{2})',           # Matches "year FY23"
                r'(\d{4}-\d{2})',              # Standalone "2022-23"
                r'(fy\d{2})',                  # Standalone "FY23"
                r'(\d{4})'                     # Standard year "2022"
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    year_str = match.group(1)
                    # Handle fiscal year format "2022-23"
                    if '-' in year_str:
                        try:
                            start_year = int(year_str.split('-')[0])
                            year = start_year
                            break
                        except:
                            continue
                    # Handle "FY23" format
                    elif year_str.lower().startswith('fy'):
                        try:
                            year_digits = int(year_str[2:])
                            year = 2000 + year_digits if year_digits < 50 else 1900 + year_digits
                            break
                        except:
                            continue
                    # Handle standard year format
                    else:
                        try:
                            year = int(year_str)
                            break
                        except:
                            continue

            print(f"DEBUG: Found business head: '{bh_name}', Year: {year}")

            # Get filtered data for business head (case-insensitive)
            bh_data = self.df[self.df[BUSINESS_HEAD_COLUMN].str.lower() == bh_name.lower()]
            print(f"DEBUG: Records for {bh_name}: {len(bh_data)}")
            
            if year:
                # Check if we have Year_Start column (from fiscal year parsing)
                if 'Year_Start' in bh_data.columns:
                    year_filtered = bh_data[bh_data['Year_Start'] == year]
                    print(f"DEBUG: Year_Start filter ({year}): {len(year_filtered)} records")
                else:
                    # Fallback to string matching if Year_Start not available
                    year_filtered = bh_data[bh_data['Year'].astype(str).str.contains(str(year))]
                    print(f"DEBUG: Year string filter ({year}): {len(year_filtered)} records")
                
                if len(year_filtered) == 0:
                    # Show available years for this business head
                    available_years = sorted(bh_data['Year_Start'].unique()) if 'Year_Start' in bh_data.columns else sorted(bh_data['Year'].unique())
                    return (f"ℹ️ No data found for {bh_name} in {year}\n"
                        f"Available years for {bh_name}: {available_years}")
                
                bh_data = year_filtered

            # Calculate comprehensive metrics
            transaction_count = len(bh_data)
            total_revenue = bh_data['TL Base Value'].sum() if len(bh_data) > 0 else 0
            total_margin = bh_data['Gross Margin Value'].sum() if len(bh_data) > 0 else 0
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            print(f"DEBUG: Final metrics - Revenue: {total_revenue}, Margin: {total_margin}, Transactions: {transaction_count}")
            
            # Handle growth query
            if 'growth' in query_lower and year:
                prev_year = year - 1
                
                current_data = self.df[
                    (self.df[BUSINESS_HEAD_COLUMN].str.lower() == bh_name.lower()) & 
                    (self.df['Year_Start'] == year)
                ]
                prev_data = self.df[
                    (self.df[BUSINESS_HEAD_COLUMN].str.lower() == bh_name.lower()) & 
                    (self.df['Year_Start'] == prev_year)
                ]
                
                if len(prev_data) == 0 or len(current_data) == 0:
                    return f"❌ Cannot calculate growth for {bh_name} in {year} - insufficient data"
                
                # Calculate revenue growth
                current_revenue = current_data['TL Base Value'].sum()
                prev_revenue = prev_data['TL Base Value'].sum()
                revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                
                # Calculate margin growth
                current_margin = current_data['Gross Margin Value'].sum()
                prev_margin = prev_data['Gross Margin Value'].sum()
                margin_growth = ((current_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                
                # Calculate transaction growth
                current_count = len(current_data)
                prev_count = len(prev_data)
                count_growth = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                return (f"📈 Business Head: {bh_name} Growth (FY{str(prev_year)[2:]}→FY{str(year)[2:]}):\n"
                    f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                    f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                    f"   • Transaction Growth: {count_growth:+.1f}%")
            
            # Determine what metric to return based on query intent
            if 'transaction' in query_lower or 'count' in query_lower:
                year_str = f" in {year}" if year else ""
                return f"📊 Transaction Count for Business Head {bh_name}{year_str}: {transaction_count:,}"
            
            elif 'revenue' in query_lower and total_revenue > 0:
                return f"💰 Business Head: {bh_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_revenue)}"
            
            elif 'margin' in query_lower and total_margin > 0:
                return f"💹 Business Head: {bh_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)"
            
            else:
                # Default comprehensive response
                year_str = f" (FY{str(year)[2:]})" if year else ""
                
                return (f"📊 {bh_name} Performance{year_str}:\n"
                    f"   • Revenue: {format_in_crores(total_revenue)}\n"
                    f"   • Gross Margin: {format_in_crores(total_margin)} (GM%: {gm_percent:.1f}%)\n"
                    f"   • Transactions: {transaction_count:,}")

        except Exception as e:
            available = self.df[BUSINESS_HEAD_COLUMN].dropna().unique()[:5] if BUSINESS_HEAD_COLUMN in self.df.columns else []
            return (f"❌ Error processing Business Head query: {str(e)}\n"
                    f"Available Business Heads: {', '.join(map(str, available))}")

    def handle_year_comparison_by_channel(self, query):
        """Handle year comparisons by channel"""
        try:
            if 'compare sales in' in query.lower() and 'by channel' in query.lower():
                # Extract years from query
                years = []
                for year in self.yearly_stats.keys():
                    if year != 'comparisons' and str(year) in query:
                        years.append(year)
                
                if len(years) < 2:
                    # Default to last 2 years if not specified
                    years = sorted([y for y in self.yearly_stats.keys() if y != 'comparisons'])[-2:]
                
                if len(years) < 2:
                    return "❌ Need at least 2 years for comparison"
                
                year1, year2 = years[0], years[1]
                
                # Get channel data for both years
                channel_data = []
                for year in [year1, year2]:
                    if 'channel_revenue' in self.yearly_stats[year]:
                        for channel, revenue in self.yearly_stats[year]['channel_revenue'].items():
                            channel_data.append({
                                'Year': year,
                                'Channel': channel,
                                'Revenue': revenue
                            })
                
                if not channel_data:
                    return "❌ No channel data available for comparison"
                
                # Create DataFrame and calculate growth
                df = pd.DataFrame(channel_data)
                df_pivot = df.pivot(index='Channel', columns='Year', values='Revenue').reset_index()
                
                # Convert to dictionary to avoid Series operations completely
                pivot_dict = df_pivot.to_dict('records')
                
                # Process each record as a dictionary
                results = []
                for record in pivot_dict:
                    channel_name = record['Channel']
                    
                    # Get values safely, defaulting to 0 if missing
                    year1_val = record.get(year1, 0)
                    year2_val = record.get(year2, 0)
                    
                    # Handle None values
                    if year1_val is None:
                        year1_val = 0
                    if year2_val is None:
                        year2_val = 0
                    
                    # Convert to float
                    year1_val = float(year1_val)
                    year2_val = float(year2_val)
                    
                    # Calculate growth
                    if year1_val == 0:
                        growth = 0 if year2_val == 0 else 999.9
                    else:
                        growth = (year2_val - year1_val) / year1_val * 100
                    
                    results.append({
                        'channel': channel_name,
                        'year1_val': year1_val,
                        'year2_val': year2_val,
                        'growth': growth
                    })
                
                # Format results
                result = f"📊 Channel Performance Comparison ({year1} vs {year2}):\n\n"
                
                plot_data_list = []
                for record in results:
                    channel_name = record['channel']
                    growth_val = record['growth']
                    year1_val = record['year1_val']
                    year2_val = record['year2_val']
                    
                    # Determine trend
                    if growth_val > 0:
                        trend = "📈"
                    elif growth_val < 0:
                        trend = "📉"
                    else:
                        trend = "➡️"
                    
                    # Format growth string
                    if abs(growth_val) < 999:
                        growth_str = f"{growth_val:+.1f}%"
                        # Add to plot data if growth is reasonable
                        plot_data_list.append({
                            'Channel': channel_name,
                            'Growth': growth_val
                        })
                    else:
                        growth_str = "New Channel" if growth_val > 0 else "Channel Removed"
                    
                    result += (f"{trend} {channel_name}: "
                            f"{format_in_crores(year1_val)} → {format_in_crores(year2_val)} "
                            f"({growth_str})\n")
                
                # Add visualization using the processed data
                if plot_data_list:
                    plot_df = pd.DataFrame(plot_data_list)
                    fig = px.bar(plot_df, x='Channel', y='Growth',
                                title=f'Channel Revenue Growth {year1} to {year2}',
                                labels={'Growth': 'Growth Percentage'})
                    fig.update_layout(yaxis_ticksuffix='%')
                    fig.show(renderer="browser")
                
                return result
            
            return None
        except Exception as e:
            return f"❌ Error in year comparison by channel: {e}"
        
    def handle_top_dimension(self, query, dimension_name, stats_dict, display_name, top_n=5):
        """Show top entities for a dimension with TL/GM metrics"""
        try:
            # Determine if we should show margin or revenue
            show_margin = 'margin' in query.lower()
            
            # Sort by margin if requested, otherwise by revenue
            sort_key = 'total_margin' if show_margin else 'total_revenue'
            top_entities = sorted(
                [(name, data[sort_key], data['total_margin']) 
                for name, data in stats_dict.items()],
                key=lambda x: x[1], 
                reverse=True
            )[:top_n]

            result = f"🏆 Top {top_n} {display_name}s by {'Margin' if show_margin else 'Revenue'}:\n\n"
            for i, (name, value, margin) in enumerate(top_entities, 1):
                result += f"{i}. {name}:\n"
                result += f"   • TL: {format_in_crores(value)}\n"
                result += f"   • GM: {format_in_crores(margin)}\n"
                
                # Calculate GM% if revenue > 0
                if value > 0:
                    gm_percent = (margin / value) * 100
                    result += f"   • GM%: {gm_percent:.1f}%\n"
                    
            return result
            
        except Exception as e:
            print(f"Error showing top {dimension_name}: {e}")
            return None
        
    def handle_dimension_query(self, query, dimension_name, stats_dict, display_name):
        """Generic handler for all dimension queries with TL, GM, Growth"""
        try:
            # Check if it's a relevant query
            if dimension_name.lower() not in query.lower():
                return None

            # Extract specific name if mentioned
            entity_name = None
            for name in stats_dict.keys():
                if str(name).lower() in query.lower():
                    entity_name = name
                    break

            # If no specific name, show top entities
            if not entity_name:
                return self.handle_top_dimension(query, dimension_name, stats_dict, display_name)

            # Get entity data
            if entity_name not in stats_dict:
                return f"❌ No data found for {display_name}: {entity_name}"

            entity_data = stats_dict[entity_name]

            # Build response header
            result = f"📊 **Performance for {display_name}: {entity_name}**\n\n"
            
            # Current period stats
            result += "💰 **Current Performance**\n"
            result += f"   • Total Revenue (TL): {format_in_crores(entity_data['total_revenue'])}\n"
            result += f"   • Gross Margin (GM): {format_in_crores(entity_data['total_margin'])}\n"
            
            # Calculate GM%
            if entity_data['total_revenue'] > 0:
                gm_percent = (entity_data['total_margin'] / entity_data['total_revenue']) * 100
                result += f"   • GM%: {gm_percent:.1f}%\n"
            
            # Yearly growth if available
            if 'yearly_revenue' in entity_data and len(entity_data['yearly_revenue']) >= 2:
                years = sorted(entity_data['yearly_revenue'].keys())
                current_year = years[-1]
                previous_year = years[-2]
                
                current_rev = entity_data['yearly_revenue'][current_year]
                previous_rev = entity_data['yearly_revenue'][previous_year]
                rev_growth = ((current_rev - previous_rev) / previous_rev * 100) if previous_rev > 0 else 0
                
                current_gm = entity_data['yearly_margin'][current_year]
                previous_gm = entity_data['yearly_margin'][previous_year]
                gm_growth = ((current_gm - previous_gm) / previous_gm * 100) if previous_gm > 0 else 0
                
                result += f"\n📈 **Growth (YoY {previous_year}→{current_year})**\n"
                result += f"   • Revenue Growth: {rev_growth:+.1f}%\n"
                result += f"   • GM Growth: {gm_growth:+.1f}%\n"

            # Add dimensional breakdowns if they exist
            breakdowns = [
                ('Region', 'regional_revenue', 'regional_margin', '🌍 Top Regions'),
                ('Vertical', 'vertical_revenue', 'vertical_margin', '🏢 Top Verticals'),
                ('Partner', 'partner_revenue', 'partner_margin', '🤝 Top Partners'),
                ('OEM', 'oem_revenue', 'oem_margin', '🏭 Top OEMs'),
                ('Channel', 'channel_revenue', 'channel_margin', '📺 Top Channels'),
                ('End Customer', 'customer_revenue', 'customer_margin', '👥 Top Customers')
            ]
            
            for dim, rev_key, margin_key, emoji in breakdowns:
                if rev_key in entity_data and entity_data[rev_key]:
                    result += f"\n{emoji}\n"
                    for item, revenue in sorted(entity_data[rev_key].items(),
                                            key=lambda x: x[1], reverse=True)[:3]:
                        margin = entity_data[margin_key][item]
                        result += f"   • {item}: TL={format_in_crores(revenue)}, GM={format_in_crores(margin)}\n"

            return result

        except Exception as e:
            print(f"Error in {dimension_name} query handling: {e}")
            return None


    def handle_personnel_query(self, query):
        try:
            personnel_roles = [
                'business head', 'group business manager', 'business manager',
                'group channel champ', 'channel champ', 'vertical champ'
            ]
            
            # Check if query is about any personnel role
            role = None
            for r in personnel_roles:
                if r in query.lower():
                    role = r.replace(' ', '_')
                    break
                    
            if not role:
                return None
                
            # Get the column name for this role
            role_column = role.title().replace('_', ' ')
            
            if role_column not in self.df.columns:
                return f"❌ No data available for {role_column}"
                
            # Extract specific name if mentioned
            names = self.processor.get_unique_values(role_column)
            mentioned_name = None
            for name in names:
                if str(name).lower() in query.lower():
                    mentioned_name = name
                    break
                    
            if mentioned_name:
                # Handle specific person query
                return self.handle_specific_personnel_query(role_column, mentioned_name, query)
            else:
                # Handle general role query
                return self.handle_general_personnel_query(role_column, query)
                
        except Exception as e:
            print(f"Error in personnel query handling: {e}")
            return None
        
    def handle_specific_personnel_query(self, role_column, name, query):
        try:
            # Filter data for this person
            person_data = self.df[self.df[role_column] == name]
            
            if person_data.empty:
                return f"❌ No data found for {name}"
                
            # Calculate core metrics
            total_revenue = person_data['TL Base Value'].sum()
            total_margin = person_data['Gross Margin Value'].sum()
            margin_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            transaction_count = len(person_data)
            avg_deal_size = total_revenue / transaction_count if transaction_count > 0 else 0
            
            # Get yearly performance data
            yearly_data = person_data.groupby(
                person_data['A/R Posting Date'].dt.to_period('Y')
            ).agg({
                'TL Base Value': 'sum',
                'Gross Margin Value': 'sum'
            }).sort_index()
            
            # Build the performance report
            report = [
                "╔══════════════════════════════════════════════════════════════╗",
                f"║                    PERFORMANCE REPORT: {name.upper():^20}                    ║",
                "╚══════════════════════════════════════════════════════════════╝",
                "",
                f"👤 Role: {role_column.replace('_', ' ').title()}",
                f"📅 Report Period: {yearly_data.index[0].strftime('%Y')} - {yearly_data.index[-1].strftime('%Y')}" if len(yearly_data) > 0 else "",
                "",
                "═" * 60,
                "📊 KEY PERFORMANCE INDICATORS",
                "═" * 60,
                f"💰 Total Revenue Generated    : {format_in_crores(total_revenue).replace('Cr', ' Crore')}",
                f"📈 Total Gross Margin        : {format_in_crores(total_margin).replace('Cr', ' Crore')} ({margin_percent:.1f}%)",
                f"🤝 Total Transactions        : {transaction_count:,} deals",
                f"💎 Average Deal Size          : {format_in_crores(avg_deal_size).replace('Cr', ' Crore')}",
                "",
                "═" * 60,
                "📈 YEARLY PERFORMANCE & GROWTH ANALYSIS",
                "═" * 60
            ]
            
            # Calculate and add yearly performance with growth
            previous_revenue = None
            previous_margin = None
            
            for i, (year, row) in enumerate(yearly_data.iterrows()):
                year_gm_percent = (row['Gross Margin Value'] / row['TL Base Value'] * 100) if row['TL Base Value'] > 0 else 0
                
                # Calculate growth rates
                revenue_growth = ""
                margin_growth = ""
                
                if previous_revenue is not None and previous_revenue > 0:
                    rev_growth_pct = ((row['TL Base Value'] - previous_revenue) / previous_revenue) * 100
                    revenue_growth = f" [{rev_growth_pct:+.1f}%]"
                    
                    # Add growth indicator
                    if rev_growth_pct > 0:
                        revenue_growth = f" 📈 [{rev_growth_pct:+.1f}%]"
                    elif rev_growth_pct < 0:
                        revenue_growth = f" 📉 [{rev_growth_pct:+.1f}%]"
                    else:
                        revenue_growth = f" ➡️ [0.0%]"
                
                if previous_margin is not None and previous_margin > 0:
                    margin_growth_pct = ((row['Gross Margin Value'] - previous_margin) / previous_margin) * 100
                    margin_growth = f" [{margin_growth_pct:+.1f}%]"
                    
                    # Add growth indicator
                    if margin_growth_pct > 0:
                        margin_growth = f" 📈 [{margin_growth_pct:+.1f}%]"
                    elif margin_growth_pct < 0:
                        margin_growth = f" 📉 [{margin_growth_pct:+.1f}%]"
                    else:
                        margin_growth = f" ➡️ [0.0%]"
                
                # Format year display
                report.extend([
                    "",
                    f"📅 FISCAL YEAR {year.strftime('%Y')}:",
                    f"   💵 Revenue     : {format_in_crores(row['TL Base Value']).replace('Cr', ' Crore')}{revenue_growth}",
                    f"   💰 Gross Margin: {format_in_crores(row['Gross Margin Value']).replace('Cr', ' Crore')} ({year_gm_percent:.1f}%){margin_growth}"
                ])
                
                # Store current values for next iteration
                previous_revenue = row['TL Base Value']
                previous_margin = row['Gross Margin Value']
            
            # Add overall growth summary if multiple years exist
            if len(yearly_data) > 1:
                first_year = yearly_data.iloc[0]
                last_year = yearly_data.iloc[-1]
                
                total_revenue_growth = ((last_year['TL Base Value'] - first_year['TL Base Value']) / first_year['TL Base Value']) * 100
                total_margin_growth = ((last_year['Gross Margin Value'] - first_year['Gross Margin Value']) / first_year['Gross Margin Value']) * 100
                
                # Calculate CAGR (Compound Annual Growth Rate)
                years_span = len(yearly_data) - 1
                revenue_cagr = (((last_year['TL Base Value'] / first_year['TL Base Value']) ** (1/years_span)) - 1) * 100 if years_span > 0 and first_year['TL Base Value'] > 0 else 0
                margin_cagr = (((last_year['Gross Margin Value'] / first_year['Gross Margin Value']) ** (1/years_span)) - 1) * 100 if years_span > 0 and first_year['Gross Margin Value'] > 0 else 0
                
                report.extend([
                    "",
                    "═" * 60,
                    "🎯 OVERALL GROWTH SUMMARY",
                    "═" * 60,
                    f"📊 Revenue Growth ({yearly_data.index[0].strftime('%Y')}-{yearly_data.index[-1].strftime('%Y')}): {total_revenue_growth:+.1f}%",
                    f"📊 Margin Growth  ({yearly_data.index[0].strftime('%Y')}-{yearly_data.index[-1].strftime('%Y')}): {total_margin_growth:+.1f}%",
                    ""
                ])
                
                if years_span > 1:
                    report.extend([
                        f"📈 Revenue CAGR: {revenue_cagr:.1f}% per year",
                        f"📈 Margin CAGR : {margin_cagr:.1f}% per year",
                        ""
                    ])
                
                # Add performance insights
                report.extend([
                    "💡 PERFORMANCE INSIGHTS:",
                    ""
                ])
                
                # Revenue trend analysis
                if total_revenue_growth > 20:
                    report.append("🌟 Exceptional revenue growth demonstrates strong market performance")
                elif total_revenue_growth > 10:
                    report.append("✅ Strong revenue growth showing positive business momentum")
                elif total_revenue_growth > 0:
                    report.append("📈 Steady revenue growth with room for acceleration")
                else:
                    report.append("🔍 Revenue decline requires strategic attention and intervention")
                
                # Margin trend analysis
                if total_margin_growth > total_revenue_growth:
                    report.append("💰 Margin growth outpacing revenue growth - excellent profitability improvement")
                elif abs(total_margin_growth - total_revenue_growth) < 5:
                    report.append("⚖️ Margin growth aligned with revenue growth - stable profitability")
                else:
                    report.append("⚠️ Margin growth lagging behind revenue - review cost optimization opportunities")
            
            report.extend([
                "",
                "═" * 60,
                "📝 Report Generated: " + pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p'),
                "═" * 60
            ])
                
            return "\n".join(report)
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
        
        # Helper functions
    def get_fiscal_year(self, date):
        """Convert date to FY2023-24 format"""
        year = date.year
        if date.month >= 4:  # April-March fiscal year
            return f"FY{year}-{str(year+1)[2:]}"
        return f"FY{year-1}-{str(year)[2:]}"
    
    def format_quarter(self, quarter_period):
        """Convert Period('Q-APR') to human-readable format (e.g., Q1: Apr-Jun 2023)"""
        start_month = (quarter_period.qyear, quarter_period.quarter * 3 - 2)  # April=1
        end_month = (quarter_period.qyear, quarter_period.quarter * 3)
        
        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
        
        # Handle year transition (e.g., Q4 is Jan-Mar of next fiscal year)
        if quarter_period.quarter == 4:
            year_str = f"{quarter_period.qyear}-{quarter_period.qyear+1}"
        else:
            year_str = str(quarter_period.qyear)
        
        return f"Q{quarter_period.quarter}: {month_names[start_month[1]-1]}-{month_names[end_month[1]-1]} {year_str}"

    def calculate_growth_metrics(self, filtered_data, dimension, value):
        """Calculate comprehensive growth metrics including quarterly, yearly, and peer comparisons"""
        try:
            metrics = {}
            
            # Quarterly growth calculations (using fiscal quarters)
            if 'Quarter' in filtered_data.columns:
                quarterly_data = filtered_data.groupby('Quarter').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum',
                    'A/R Posting Date': 'count'
                }).sort_index()
                
                if len(quarterly_data) >= 2:
                    # Quarter-over-Quarter growth (most recent vs previous quarter)
                    quarters = sorted(quarterly_data.index)
                    if len(quarters) >= 2:
                        current_quarter = quarters[-1]
                        prev_quarter = quarters[-2]
                        
                        current_rev = quarterly_data.loc[current_quarter, 'TL Base Value']
                        prev_rev = quarterly_data.loc[prev_quarter, 'TL Base Value']
                        qoq_rev_growth = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                        
                        current_gm = quarterly_data.loc[current_quarter, 'Gross Margin Value']
                        prev_gm = quarterly_data.loc[prev_quarter, 'Gross Margin Value']
                        qoq_gm_growth = ((current_gm - prev_gm) / prev_gm * 100) if prev_gm > 0 else 0
                        
                        current_q_str = self.format_quarter(current_quarter)
                        prev_q_str = self.format_quarter(prev_quarter)
                        
                        metrics[f"QoQ Growth ({prev_q_str}→{current_q_str}) - Revenue"] = qoq_rev_growth
                        metrics[f"QoQ Growth ({prev_q_str}→{current_q_str}) - Gross Margin"] = qoq_gm_growth
                    
                    # Year-over-Year quarterly growth (same quarter previous year)
                    if len(quarters) >= 4:  # Need at least 4 quarters for YoY comparison
                        current_quarter = quarters[-1]
                        # Find same quarter from previous year (4 quarters back)
                        prev_year_quarter = None
                        for i, quarter in enumerate(quarters[:-4]):
                            if quarter.quarter == current_quarter.quarter:
                                prev_year_quarter = quarter
                                break
                        
                        if prev_year_quarter and prev_year_quarter in quarterly_data.index:
                            current_rev = quarterly_data.loc[current_quarter, 'TL Base Value']
                            prev_year_rev = quarterly_data.loc[prev_year_quarter, 'TL Base Value']
                            yoy_rev_growth = ((current_rev - prev_year_rev) / prev_year_rev * 100) if prev_year_rev > 0 else 0
                            
                            current_gm = quarterly_data.loc[current_quarter, 'Gross Margin Value']
                            prev_year_gm = quarterly_data.loc[prev_year_quarter, 'Gross Margin Value']
                            yoy_gm_growth = ((current_gm - prev_year_gm) / prev_year_gm * 100) if prev_year_gm > 0 else 0
                            
                            current_q_str = self.format_quarter(current_quarter)
                            prev_q_str = self.format_quarter(prev_year_quarter)
                            
                            metrics[f"YoY Quarterly Growth ({prev_q_str}→{current_q_str}) - Revenue"] = yoy_rev_growth
                            metrics[f"YoY Quarterly Growth ({prev_q_str}→{current_q_str}) - Gross Margin"] = yoy_gm_growth
            
            # Yearly growth using Fiscal Year data
            if 'Fiscal Year' in filtered_data.columns:
                yearly_data = filtered_data.groupby('Fiscal Year').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum',
                    'A/R Posting Date': 'count'
                }).sort_index()
                
                if len(yearly_data) >= 2:
                    years = sorted(yearly_data.index)
                    current_year = years[-1]
                    prev_year = years[-2]
                    
                    current_rev = yearly_data.loc[current_year, 'TL Base Value']
                    prev_rev = yearly_data.loc[prev_year, 'TL Base Value']
                    rev_growth = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                    
                    current_gm = yearly_data.loc[current_year, 'Gross Margin Value']
                    prev_gm = yearly_data.loc[prev_year, 'Gross Margin Value']
                    gm_growth = ((current_gm - prev_gm) / prev_gm * 100) if prev_gm > 0 else 0
                    
                    metrics[f"YoY Growth ({prev_year}→{current_year}) - Revenue"] = rev_growth
                    metrics[f"YoY Growth ({prev_year}→{current_year}) - Gross Margin"] = gm_growth
            
            # Fallback to Year_Start if Fiscal Year not available
            elif 'Year_Start' in filtered_data.columns:
                yearly_data = filtered_data.groupby('Year_Start').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum',
                    'A/R Posting Date': 'count'
                }).sort_index()
                
                if len(yearly_data) >= 2:
                    years = sorted(yearly_data.index)
                    current_year = years[-1]
                    prev_year = years[-2]
                    
                    current_rev = yearly_data.loc[current_year, 'TL Base Value']
                    prev_rev = yearly_data.loc[prev_year, 'TL Base Value']
                    rev_growth = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                    
                    current_gm = yearly_data.loc[current_year, 'Gross Margin Value']
                    prev_gm = yearly_data.loc[prev_year, 'Gross Margin Value']
                    gm_growth = ((current_gm - prev_gm) / prev_gm * 100) if prev_gm > 0 else 0
                    
                    metrics[f"YoY Growth ({prev_year}→{current_year}) - Revenue"] = rev_growth
                    metrics[f"YoY Growth ({prev_year}→{current_year}) - Gross Margin"] = gm_growth
            
            # Regional growth analysis
            if 'Region' in filtered_data.columns:
                regional_data = filtered_data.groupby('Region').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_values('TL Base Value', ascending=False)
                
                if len(regional_data) >= 1:
                    top_region = regional_data.index[0]
                    top_region_rev = regional_data.iloc[0]['TL Base Value']
                    top_region_percent = (top_region_rev / filtered_data['TL Base Value'].sum() * 100) if filtered_data['TL Base Value'].sum() > 0 else 0
                    metrics["Top Region Contribution"] = f"{top_region} ({top_region_percent:.1f}%)"
            
            # Peer comparison analysis
            if dimension in self.df.columns:
                # Get all people in same role (excluding current person)
                peers_data = self.df[self.df[dimension] != value]
                if not peers_data.empty:
                    peers_rev = peers_data['TL Base Value'].sum()
                    peers_gm = peers_data['Gross Margin Value'].sum()
                    
                    person_rev = filtered_data['TL Base Value'].sum()
                    person_gm = filtered_data['Gross Margin Value'].sum()
                    
                    # Calculate market share among peers
                    total_rev = person_rev + peers_rev
                    total_gm = person_gm + peers_gm
                    
                    rev_share = (person_rev / total_rev * 100) if total_rev > 0 else 0
                    gm_share = (person_gm / total_gm * 100) if total_gm > 0 else 0
                    
                    metrics["Revenue Share Among Peers"] = f"{rev_share:.1f}%"
                    metrics["Gross Margin Share Among Peers"] = f"{gm_share:.1f}%"
                    
                    # Performance ranking among peers
                    all_people_data = self.df.groupby(dimension).agg({
                        'TL Base Value': 'sum',
                        'Gross Margin Value': 'sum'
                    }).sort_values('TL Base Value', ascending=False)
                    
                    if value in all_people_data.index:
                        rank = list(all_people_data.index).index(value) + 1
                        total_people = len(all_people_data)
                        metrics["Performance Rank"] = f"{rank} out of {total_people}"
            
            # Average deal size and margin analysis
            if len(filtered_data) > 0:
                avg_deal_size = filtered_data['TL Base Value'].mean()
                avg_margin = filtered_data['Gross Margin Value'].mean()
                avg_margin_percent = (filtered_data['Gross Margin Value'].sum() / filtered_data['TL Base Value'].sum() * 100) if filtered_data['TL Base Value'].sum() > 0 else 0
                
                metrics["Average Deal Size"] = f"{format_in_crores(avg_deal_size)}"
                metrics["Average Margin %"] = f"{avg_margin_percent:.1f}%"
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating growth metrics: {e}")
            return {}
        
    def handle_general_personnel_query(self, role_column, query):
        try:
            # Get top performers in this role
            top_performers = self.df.groupby(role_column).agg({
                'TL Base Value': 'sum',
                'Gross Margin Value': 'sum'
            }).sort_values('TL Base Value', ascending=False).head(10)
            
            if top_performers.empty:
                return f"❌ No data available for {role_column}"
                
            result = f"🏆 **Top {role_column}s by Revenue:**\n\n"
            for name, row in top_performers.iterrows():
                result += f"   • {name}: {format_in_crores(row['TL Base Value'])} (GM: {format_in_crores(row['Gross Margin Value'])})\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error processing personnel query: {e}"


    def handle_partner_query(self, query):
        """Handle partner-related queries with comprehensive multi-year and regional analysis using interactive HTML tables"""
        try:
            print(f"DEBUG: Partner handler called with: {query}")
            
            # Extract partner name from query - improved regex patterns
            query_lower = query.lower()
            partner_match = None
            
            # Try multiple regex patterns for partner extraction
            patterns = [
                r'partner\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'partner\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+partner\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|performance).*?(?:for|of)\s+([^,\n]+?)(?:\s+partner|$)'
            ]
            
            for pattern in patterns:
                partner_match = re.search(pattern, query_lower)
                if partner_match:
                    print(f"DEBUG: Partner extracted with pattern: {pattern}")
                    break
            
            # If no regex match, try direct matching with available partners
            if not partner_match:
                print("DEBUG: No regex match, trying direct partner matching")
                available_partners = self.df['Partner'].dropna().unique()
                matched_directly = None
                for partner in available_partners:
                    if str(partner).lower() in query_lower:
                        matched_directly = partner
                        print(f"DEBUG: Direct match found: {partner}")
                        break
                
                # Create a simple object with group method if we found a direct match
                if matched_directly:
                    class DirectMatch:
                        def __init__(self, value):
                            self.value = value
                        def group(self, index):
                            return self.value
                    partner_match = DirectMatch(matched_directly)
            
            if not partner_match:
                print("DEBUG: No partner match found")
                available_partners = self.df['Partner'].dropna().unique()
                return (f"❌ Please specify a partner name.\n"
                        f"Available: {', '.join(map(str, available_partners[:5]))}")
            
            requested_partner = partner_match.group(1).strip()
            print(f"DEBUG: Extracted partner: '{requested_partner}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_partner = None
            available_partners = self.df['Partner'].dropna().unique()
            
            print(f"DEBUG: Available partners: {list(available_partners)}")
            
            # Try exact match first
            for partner in available_partners:
                if str(partner).lower().strip() == requested_partner.lower().strip():
                    matched_partner = partner
                    print(f"DEBUG: Exact match found: {matched_partner}")
                    break
            
            # Try partial match if exact fails
            if not matched_partner:
                for partner in available_partners:
                    if requested_partner.lower().strip() in str(partner).lower().strip():
                        matched_partner = partner
                        print(f"DEBUG: Partial match found: {matched_partner}")
                        break
            
            if not matched_partner:
                print(f"DEBUG: No match found for '{requested_partner}'")
                return (f"❌ Partner '{requested_partner}' not found.\n"
                        f"Available: {', '.join(map(str, available_partners[:5]))}")
            
            # Get all data for this partner
            partner_data = self.df[self.df['Partner'] == matched_partner]
            available_years = sorted(partner_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for partner {matched_partner}"
            
            print(f"DEBUG: Available years for {matched_partner}: {available_years}")
            
            # Check if end customer data is available
            customer_column = None
            possible_customer_columns = ['End Customer Name', 'End Customer', 'Customer Name', 'Customer', 'End_Customer_Name']
            for col in possible_customer_columns:
                if col in self.df.columns:
                    customer_column = col
                    print(f"DEBUG: Found customer column: {customer_column}")
                    break
            
            if not customer_column:
                print(f"DEBUG: No customer column found. Available columns: {list(self.df.columns)}")
                # Still continue but without customer data
            
            # Build comprehensive output with interactive HTML tables
            output_text = f"## PERFORMANCE FOR {matched_partner.upper()} PARTNER\n\n"
            
            # Year-wise performance summary table
            yearly_summary_data = []
            yearly_customer_data = {}  # Store customer data for each year
            
            for year in available_years:
                year_data = partner_data[partner_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = partner_data[partner_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(year_data)
                
                # Get top 5 end customers for this year
                year_customers = []
                if customer_column and customer_column in year_data.columns:
                    print(f"DEBUG: Processing customers for year {year}")
                    customer_stats = year_data[year_data[customer_column].notna()].groupby(customer_column).agg(
                        Revenue=('TL Base Value', 'sum'),
                        Margin=('Gross Margin Value', 'sum'),
                        Transactions=('TL Base Value', 'count')
                    ).reset_index().sort_values('Revenue', ascending=False).head(5)
                    
                    print(f"DEBUG: Found {len(customer_stats)} customers for year {year}")
                    
                    for _, customer_row in customer_stats.iterrows():
                        customer_gm_percent = (customer_row['Margin'] / customer_row['Revenue'] * 100) if customer_row['Revenue'] > 0 else 0
                        year_customers.append({
                            'name': str(customer_row[customer_column])[:25],  # Truncate long names
                            'revenue': f"₹{customer_row['Revenue']/10000000:.2f}Cr",
                            'margin': f"₹{customer_row['Margin']/10000000:.2f}Cr",
                            'gm_percent': f"{customer_gm_percent:.1f}%",
                            'transactions': f"{int(customer_row['Transactions']):,}"
                        })
                        print(f"DEBUG: Added customer: {customer_row[customer_column]}")
                else:
                    print(f"DEBUG: No customer column or no data for year {year}")
                
                yearly_customer_data[year] = year_customers
                print(f"DEBUG: Year {year} has {len(year_customers)} customers")
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                txn_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    prev_count = len(prev_year_data)
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                    
                    if prev_count > 0:
                        txn_growth = ((transaction_count - prev_count) / prev_count * 100)
                        txn_growth_str = f"{txn_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'Transactions': f"{transaction_count:,}",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str,
                    'Txn Growth': txn_growth_str,
                    'year_key': year  # For linking with customer data
                })
            
            # Create interactive yearly summary table
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_interactive_html_table(
                    yearly_df,
                    yearly_customer_data,
                    table_id=f"{matched_partner.lower()}_yearly_summary",
                    title=f"{matched_partner} Partner - Yearly Performance",
                    table_type="yearly",
                    detail_type="customers"
                )
                output_text += yearly_table_html + "\n\n"
            
            # Regional Analysis Section
            region_column = 'Region'
            if region_column in partner_data.columns:
                output_text += "### REGIONAL PERFORMANCE\n\n"
                
                # Regional summary for each year
                for year in available_years:
                    year_data = partner_data[partner_data['Year_Start'] == year]
                    prev_year_data = partner_data[partner_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty regions
                    year_filtered = year_data[year_data[region_column].notna() & (year_data[region_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats by region
                    current_stats = year_filtered.groupby(region_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum'),
                        Txn_Current=('TL Base Value', 'count')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Get customer data for each region
                    regional_customer_data = {}
                    for _, region_row in current_stats.iterrows():
                        region_name = region_row[region_column]
                        region_data = year_filtered[year_filtered[region_column] == region_name]
                        
                        region_customers = []
                        if customer_column and customer_column in region_data.columns:
                            print(f"DEBUG: Processing customers for region {region_name} in year {year}")
                            customer_stats = region_data[region_data[customer_column].notna()].groupby(customer_column).agg(
                                Revenue=('TL Base Value', 'sum'),
                                Margin=('Gross Margin Value', 'sum'),
                                Transactions=('TL Base Value', 'count')
                            ).reset_index().sort_values('Revenue', ascending=False).head(5)
                            
                            print(f"DEBUG: Found {len(customer_stats)} customers for region {region_name}")
                            
                            for _, customer_row in customer_stats.iterrows():
                                customer_gm_percent = (customer_row['Margin'] / customer_row['Revenue'] * 100) if customer_row['Revenue'] > 0 else 0
                                region_customers.append({
                                    'name': str(customer_row[customer_column])[:25],
                                    'revenue': f"₹{customer_row['Revenue']/10000000:.2f}Cr",
                                    'margin': f"₹{customer_row['Margin']/10000000:.2f}Cr",
                                    'gm_percent': f"{customer_gm_percent:.1f}%",
                                    'transactions': f"{int(customer_row['Transactions']):,}"
                                })
                        else:
                            print(f"DEBUG: No customer column or no data for region {region_name}")
                        
                        regional_customer_data[region_name] = region_customers
                        print(f"DEBUG: Region {region_name} has {len(region_customers)} customers")
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and region_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[region_column].notna() & (prev_year_data[region_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(region_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum'),
                                Txn_Prev=('TL Base Value', 'count')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=region_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        merged_stats['Txn_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        region_name = str(row[region_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        txn_prev_val = float(row['Txn_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        txn_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        if txn_prev_val > 0:
                            txn_growth = (row['Txn_Current'] - txn_prev_val) / txn_prev_val * 100
                            txn_growth_str = f"{txn_growth:+.1f}%"
                        elif row['Txn_Current'] > 0:
                            txn_growth_str = "New"
                        
                        table_data.append({
                            'Region': region_name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Transactions': f"{int(row['TL_Current']):,}",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str,
                            'Txn Growth': txn_growth_str,
                            'region_key': str(row[region_column])  # For linking with customer data
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        output_text += f"**{year_str}:**\n\n"
                        
                        # Create DataFrame and generate interactive HTML table
                        region_df = pd.DataFrame(table_data)
                        table_html = self._generate_interactive_html_table(
                            region_df,
                            regional_customer_data,
                            table_id=f"{matched_partner.lower()}_regional_{year}",
                            title=f"Regional Performance - {year_str}",
                            table_type="regional"
                        )
                        output_text += table_html + "\n\n"
            else:
                output_text += "### REGIONAL PERFORMANCE\n❌ Region column not found in data\n\n"
            
            print(f"DEBUG: Generated comprehensive interactive HTML table report for {matched_partner}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing partner query: {str(e)}"
        
    
        
    def handle_oem_query(self, query):
        """Handle OEM specific queries with comprehensive multi-year and regional analysis using interactive HTML tables"""
        try:
            print(f"DEBUG: OEM handler called with: {query}")
            
            # Check if OEM column exists
            oem_column = 'OEM'
            if oem_column not in self.df.columns:
                print("DEBUG: No OEM column found")
                return "❌ OEM data not available in this dataset"
            
            print(f"DEBUG: Available columns: {list(self.df.columns)}")
            
            # Extract OEM name from query - improved regex patterns
            query_lower = query.lower()
            oem_match = None
            
            # Try multiple regex patterns for OEM extraction
            patterns = [
                r'oem\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'oem\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+oem\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|performance).*?(?:for|of)\s+([^,\n]+?)(?:\s+oem|$)'
            ]
            
            for pattern in patterns:
                oem_match = re.search(pattern, query_lower)
                if oem_match:
                    print(f"DEBUG: OEM extracted with pattern: {pattern}")
                    break
            
            # If no regex match, try direct matching with available OEMs
            if not oem_match:
                print("DEBUG: No regex match, trying direct OEM matching")
                available_oems = self.df[oem_column].dropna().unique()
                matched_directly = None
                for oem in available_oems:
                    if oem.lower() in query_lower:
                        matched_directly = oem
                        print(f"DEBUG: Direct match found: {oem}")
                        break
                
                # Create a simple object with group method if we found a direct match
                if matched_directly:
                    class DirectMatch:
                        def __init__(self, value):
                            self.value = value
                        def group(self, index):
                            return self.value
                    oem_match = DirectMatch(matched_directly)
            
            if not oem_match:
                print("DEBUG: No OEM match found")
                available_oems = self.df[oem_column].dropna().unique()
                return (f"❌ Please specify an OEM name.\n"
                        f"Available: {', '.join(map(str, available_oems[:5]))}")
            
            requested_oem = oem_match.group(1).strip()
            print(f"DEBUG: Extracted OEM: '{requested_oem}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_oem = None
            available_oems = self.df[oem_column].dropna().unique()
            
            print(f"DEBUG: Available OEMs: {list(available_oems)}")
            
            # Try exact match first
            for oem in available_oems:
                if str(oem).lower().strip() == requested_oem.lower().strip():
                    matched_oem = oem
                    print(f"DEBUG: Exact match found: {matched_oem}")
                    break
            
            # Try partial match if exact fails
            if not matched_oem:
                for oem in available_oems:
                    if requested_oem.lower().strip() in str(oem).lower().strip():
                        matched_oem = oem
                        print(f"DEBUG: Partial match found: {matched_oem}")
                        break
            
            if not matched_oem:
                print(f"DEBUG: No match found for '{requested_oem}'")
                return (f"❌ OEM '{requested_oem}' not found.\n"
                        f"Available: {', '.join(map(str, available_oems[:5]))}")
            
            # Get all data for this OEM
            oem_data = self.df[self.df[oem_column] == matched_oem]
            available_years = sorted(oem_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for OEM {matched_oem}"
            
            print(f"DEBUG: Available years for {matched_oem}: {available_years}")
            
            # Check if partner data is available
            partner_column = None
            possible_partner_columns = ['Partner Name', 'Partner', 'Channel Partner', 'Reseller', 'Distributor']
            for col in possible_partner_columns:
                if col in self.df.columns:
                    partner_column = col
                    break
            
            # Build comprehensive output with interactive HTML tables
            output_text = f"## PERFORMANCE FOR {matched_oem.upper()} OEM\n\n"
            
            # Year-wise performance summary table
            yearly_summary_data = []
            yearly_partner_data = {}  # Store partner data for each year
            
            for year in available_years:
                year_data = oem_data[oem_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = oem_data[oem_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(year_data)
                
                # Get top 5 partners for this year
                year_partners = []
                if partner_column and partner_column in year_data.columns:
                    partner_stats = year_data[year_data[partner_column].notna()].groupby(partner_column).agg(
                        Revenue=('TL Base Value', 'sum'),
                        Margin=('Gross Margin Value', 'sum'),
                        Transactions=('TL Base Value', 'count')
                    ).reset_index().sort_values('Revenue', ascending=False).head(5)
                    
                    for _, partner_row in partner_stats.iterrows():
                        partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                        year_partners.append({
                            'name': str(partner_row[partner_column])[:25],  # Truncate long names
                            'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                            'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                            'gm_percent': f"{partner_gm_percent:.1f}%",
                            'transactions': f"{int(partner_row['Transactions']):,}"
                        })
                
                yearly_partner_data[year] = year_partners
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                txn_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    prev_count = len(prev_year_data)
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                    
                    if prev_count > 0:
                        txn_growth = ((transaction_count - prev_count) / prev_count * 100)
                        txn_growth_str = f"{txn_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'Transactions': f"{transaction_count:,}",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str,
                    'Txn Growth': txn_growth_str,
                    'year_key': year  # For linking with partner data
                })
            
            # Create interactive yearly summary table
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_interactive_html_table(
                    yearly_df,
                    yearly_partner_data,
                    table_id=f"{matched_oem.lower()}_yearly_summary",
                    title=f"{matched_oem} OEM - Yearly Performance",
                    table_type="yearly"
                )
                output_text += yearly_table_html + "\n\n"
            
            # Regional Analysis Section
            region_column = 'Region'
            if region_column in oem_data.columns:
                output_text += "### REGIONAL PERFORMANCE\n\n"
                
                # Regional summary for each year
                for year in available_years:
                    year_data = oem_data[oem_data['Year_Start'] == year]
                    prev_year_data = oem_data[oem_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty regions
                    year_filtered = year_data[year_data[region_column].notna() & (year_data[region_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats by region
                    current_stats = year_filtered.groupby(region_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum'),
                        Txn_Current=('TL Base Value', 'count')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Get partner data for each region
                    regional_partner_data = {}
                    for _, region_row in current_stats.iterrows():
                        region_name = region_row[region_column]
                        region_data = year_filtered[year_filtered[region_column] == region_name]
                        
                        region_partners = []
                        if partner_column and partner_column in region_data.columns:
                            partner_stats = region_data[region_data[partner_column].notna()].groupby(partner_column).agg(
                                Revenue=('TL Base Value', 'sum'),
                                Margin=('Gross Margin Value', 'sum'),
                                Transactions=('TL Base Value', 'count')
                            ).reset_index().sort_values('Revenue', ascending=False).head(5)
                            
                            for _, partner_row in partner_stats.iterrows():
                                partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                                region_partners.append({
                                    'name': str(partner_row[partner_column])[:25],
                                    'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                                    'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                                    'gm_percent': f"{partner_gm_percent:.1f}%",
                                    'transactions': f"{int(partner_row['Transactions']):,}"
                                })
                        
                        regional_partner_data[region_name] = region_partners
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and region_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[region_column].notna() & (prev_year_data[region_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(region_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum'),
                                Txn_Prev=('TL Base Value', 'count')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=region_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        merged_stats['Txn_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        region_name = str(row[region_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        txn_prev_val = float(row['Txn_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        txn_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        if txn_prev_val > 0:
                            txn_growth = (row['Txn_Current'] - txn_prev_val) / txn_prev_val * 100
                            txn_growth_str = f"{txn_growth:+.1f}%"
                        elif row['Txn_Current'] > 0:
                            txn_growth_str = "New"
                        
                        table_data.append({
                            'Region': region_name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Transactions': f"{int(row['Txn_Current']):,}",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str,
                            'Txn Growth': txn_growth_str,
                            'region_key': str(row[region_column])  # For linking with partner data
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        output_text += f"**{year_str}:**\n\n"
                        
                        # Create DataFrame and generate interactive HTML table
                        region_df = pd.DataFrame(table_data)
                        table_html = self._generate_interactive_html_table(
                            region_df,
                            regional_partner_data,
                            table_id=f"{matched_oem.lower()}_regional_{year}",
                            title=f"Regional Performance - {year_str}",
                            table_type="regional"
                        )
                        output_text += table_html + "\n\n"
            else:
                output_text += "### REGIONAL PERFORMANCE\n❌ Region column not found in data\n\n"
            
            print(f"DEBUG: Generated comprehensive interactive HTML table report for {matched_oem}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing OEM query: {str(e)}"

    def _generate_interactive_html_table(self, df, expandable_data, table_id, title, table_type="yearly", detail_type="partners", highlight_total=False):
        """Generate an interactive HTML table with expandable rows showing detailed information
        
        Args:
            df: DataFrame with main table data
            expandable_data: Dictionary containing data for expandable rows
            table_id: Unique identifier for the table
            title: Table title
            table_type: "yearly" or "regional" 
            detail_type: "partners" or "customers" - what to show in expandable rows
            highlight_total: Whether to highlight total row
        """
        
        if df.empty:
            return f"<p>No data available for {title}</p>"
        
        # Generate unique table ID
        unique_id = f"{table_id}_{hash(title) % 10000}"
        
        # Set labels based on detail type
        if detail_type == "partners":
            detail_label = "Top 5 Partners:"
        elif detail_type == "customers":
            detail_label = "Top 5 End Customers:"
        else:
            detail_label = f"Top 5 {detail_type.title()}:"
        
        button_title_show = f"Show top 5 {detail_type}"
        button_title_hide = f"Hide {detail_type} details"
        
        html = f"""
        <div class="interactive-table-container" id="container_{unique_id}">
            <h4 class="table-title">{title}</h4>
            <table class="data-table interactive-table" id="{unique_id}">
                <thead>
                    <tr>
        """
        
        # Add expand column header
        html += '<th class="expand-column">Details</th>'
        
        # Add regular column headers
        for col in df.columns:
            if col not in ['year_key', 'region_key']:  # Skip metadata columns
                html += f'<th>{col}</th>'
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add table rows
        for idx, row in df.iterrows():
            row_id = f"row_{unique_id}_{idx}"
            
            # Determine the key for expandable data lookup
            if table_type == "yearly":
                data_key = row.get('year_key', None)
            else:  # regional
                data_key = row.get('region_key', None)
            
            # Check if expandable data exists for this row
            has_details = data_key in expandable_data and len(expandable_data[data_key]) > 0
            
            html += f'<tr class="main-row" data-row-id="{row_id}">'
            
            # Add expand/collapse button
            if has_details:
                html += f'''
                    <td class="expand-cell">
                        <button class="expand-btn" onclick="toggleDetails('{row_id}')" title="{button_title_show}">
                            <span class="expand-icon">+</span>
                        </button>
                    </td>
                '''
            else:
                html += '<td class="expand-cell"><span class="no-data">—</span></td>'
            
            # Add regular data columns
            for col in df.columns:
                if col not in ['year_key', 'region_key']:  # Skip metadata columns
                    cell_value = str(row[col])
                    
                    # Apply special styling for growth values
                    cell_class = ""
                    if 'growth' in col.lower() and cell_value not in ['N/A', 'New']:
                        if cell_value.startswith('+'):
                            cell_class = 'class="positive-growth"'
                        elif cell_value.startswith('-'):
                            cell_class = 'class="negative-growth"'
                    
                    html += f'<td {cell_class}>{cell_value}</td>'
            
            html += '</tr>'
            
            # Add expandable details row (initially hidden)
            if has_details:
                html += f'''
                    <tr class="detail-row" id="details_{row_id}" style="display: none;">
                        <td colspan="{len(df.columns)}">
                            <div class="detail-content">
                                <h5>{detail_label}</h5>
                                <div class="detail-cards">
                '''
                
                for i, item in enumerate(expandable_data[data_key]):
                    rank = i + 1
                    html += f'''
                        <div class="detail-card rank-{rank}">
                            <div class="detail-rank">#{rank}</div>
                            <div class="detail-info">
                                <div class="detail-name">{item['name']}</div>
                                <div class="detail-metrics">
                                    <span class="metric"><strong>Revenue:</strong> {item['revenue']}</span>
                                    <span class="metric"><strong>Margin:</strong> {item['margin']}</span>
                                    <span class="metric"><strong>GM%:</strong> {item['gm_percent']}</span>
                                    <span class="metric"><strong>Transactions:</strong> {item['transactions']}</span>
                                </div>
                            </div>
                        </div>
                    '''
                
                html += '''
                                </div>
                            </div>
                        </td>
                    </tr>
                '''
        
        html += """
                </tbody>
            </table>
        </div>
        
        <script>
        function toggleDetails(rowId) {
            const detailsRow = document.getElementById('details_' + rowId);
            const expandBtn = document.querySelector(`[data-row-id="${rowId}"] .expand-btn`);
            const expandIcon = expandBtn.querySelector('.expand-icon');
            
            if (detailsRow.style.display === 'none') {
                detailsRow.style.display = 'table-row';
                expandIcon.textContent = '−';
                expandIcon.style.transform = 'rotate(0deg)';
                expandBtn.setAttribute('title', '""" + button_title_hide + """');
            } else {
                detailsRow.style.display = 'none';
                expandIcon.textContent = '+';
                expandIcon.style.transform = 'rotate(0deg)';
                expandBtn.setAttribute('title', '""" + button_title_show + """');
            }
        }
        </script>
        
        <style>
        .interactive-table-container {
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            background: white;
        }
        
        .table-title {
            color: #1e293b !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            margin: 0 !important;
            padding: 12px 15px !important;
            background-color: #f8fafc !important;
            border-bottom: 2px solid #e2e8f0 !important;
        }
        
        .interactive-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .expand-column {
            width: 60px !important;
            background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
            text-align: center !important;
        }
        
        .expand-cell {
            text-align: center;
            padding: 8px 4px !important;
            background-color: #f8fafc;
            border-right: 2px solid #e2e8f0;
        }
        
        .expand-btn {
            background: linear-gradient(135deg, #10a37f 0%, #0e8f6f 100%);
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .expand-btn:hover {
            background: linear-gradient(135deg, #0e8f6f 0%, #0c7a5f 100%);
            transform: scale(1.1);
            box-shadow: 0 3px 6px rgba(0,0,0,0.3);
        }
        
        .expand-icon {
            font-size: 14px;
            line-height: 1;
            transition: transform 0.3s ease;
        }
        
        .no-data {
            color: #9ca3af;
            font-size: 14px;
        }
        
        .detail-row {
            background-color: #f1f5f9 !important;
        }
        
        .detail-content {
            padding: 15px;
            border-left: 4px solid #10a37f;
        }
        
        .detail-content h5 {
            margin: 0 0 12px 0;
            color: #1e293b;
            font-size: 14px;
            font-weight: 600;
        }
        
        .detail-cards {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .detail-card {
            background: white;
            border-radius: 6px;
            padding: 10px;
            min-width: 200px;
            flex: 1;
            border-left: 4px solid #cbd5e1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        
        .detail-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 8px rgba(0,0,0,0.15);
        }
        
        .detail-card.rank-1 { border-left-color: #fbbf24; }
        .detail-card.rank-2 { border-left-color: #9ca3af; }
        .detail-card.rank-3 { border-left-color: #f97316; }
        .detail-card.rank-4 { border-left-color: #10a37f; }
        .detail-card.rank-5 { border-left-color: #3b82f6; }
        
        .detail-rank {
            font-size: 11px;
            font-weight: bold;
            color: #64748b;
            margin-bottom: 5px;
        }
        
        .detail-name {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            font-size: 12px;
        }
        
        .detail-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
            font-size: 10px;
        }
        
        .metric {
            color: #475569;
            padding: 2px 0;
        }
        
        .metric strong {
            color: #334155;
        }
        
        .positive-growth {
            color: #10a37f !important;
            font-weight: 600 !important;
        }
        
        .negative-growth {
            color: #ef4444 !important;
            font-weight: 600 !important;
        }
        
        @media (max-width: 768px) {
            .detail-cards {
                flex-direction: column;
            }
            
            .detail-card {
                min-width: auto;
            }
            
            .detail-metrics {
                grid-template-columns: 1fr;
            }
            
            .expand-btn {
                width: 20px;
                height: 20px;
            }
            
            .expand-icon {
                font-size: 12px;
            }
        }
        </style>
        """
        
        return html
        
    def handle_oem_region_query(self, query):
        """Handle OEM-specific regional queries with proper filtering"""
        try:
            # Check if this is an OEM + region query
            if 'oem' not in query.lower() or 'region' not in query.lower():
                return None

            # Extract OEM name (case-insensitive exact match)
            oem_name = None
            possible_oems = self.df['OEM'].dropna().unique()
            for oem in possible_oems:
                if re.search(rf'\b{re.escape(str(oem).lower())}\b', query.lower()):
                    oem_name = oem
                    break

            if not oem_name:
                return "❌ Please specify a valid OEM name"

            # Extract region name (case-insensitive exact match)
            region_name = None
            possible_regions = self.df['Region'].dropna().unique()
            for region in possible_regions:
                if re.search(rf'\b{re.escape(str(region).lower())}\b', query.lower()):
                    region_name = region
                    break

            if not region_name:
                return "❌ Please specify a valid region"

            # Extract year if specified
            year = None
            year_match = re.search(r'(?:fy)?(20)?(\d{2})', query.lower())
            if year_match:
                year = 2000 + int(year_match.group(2))  # Handles both FY22 and 2022

            # Filter data - exact matches for OEM and Region
            mask = (
                (self.df['OEM'].str.lower() == str(oem_name).lower()) & 
                (self.df['Region'].str.lower() == str(region_name).lower())
            )
            if year:
                mask &= (self.df['Year_Start'] == year)

            filtered_data = self.df[mask]

            if len(filtered_data) == 0:
                year_str = f" in {year}" if year else ""
                return f"❌ No transactions found for {oem_name} in {region_name}{year_str}"

            # Calculate metrics
            transaction_count = len(filtered_data)
            total_revenue = filtered_data['TL Base Value'].sum()
            total_margin = filtered_data['Gross Margin Value'].sum()
            gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

            # Format response
            year_str = f" (FY{str(year)[2:]})" if year else ""
            return (
                f"📊 {oem_name} in {region_name}{year_str}:\n"
                f"   • Transactions: {transaction_count:,}\n"
                f"   • Revenue: {format_in_crores(total_revenue)}\n"
                f"   • Gross Margin: {format_in_crores(total_margin)} ({gm_percent:.1f}%)"
            )

        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    
    def _calculate_oem_growth(self, oem_name, prev_data, current_data, year1, year2):
        """Calculate growth metrics between two years for a specific OEM"""
        try:
            # Calculate metrics for both periods
            prev_revenue = prev_data['TL Base Value'].sum()
            current_revenue = current_data['TL Base Value'].sum()
            revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            prev_margin = prev_data['Gross Margin Value'].sum()
            current_margin = current_data['Gross Margin Value'].sum()
            margin_growth = ((current_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
            
            prev_count = len(prev_data)
            current_count = len(current_data)
            count_growth = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0

            # Format results
            result = (f"📈 {oem_name} Growth (FY{str(year1)[2:]} → FY{str(year2)[2:]}):\n\n"
                    f"💰 Revenue Growth: {revenue_growth:+.1f}%\n"
                    f"   (Change: {format_in_crores(current_revenue - prev_revenue)})\n"
                    f"💹 Gross Margin Growth: {margin_growth:+.1f}%\n"
                    f"   (Change: {format_in_crores(current_margin - prev_margin)})\n"
                    f"📊 Transaction Growth: {count_growth:+.1f}%\n"
                    f"   (Change: {current_count - prev_count:+,} transactions)")
            
            return result
        except Exception as e:
            return f"❌ Error calculating growth: {str(e)}"

    def _handle_top_oems(self, query):
        """Handle queries about top OEMs (renamed from handle_top_oems)"""
        try:
            # Determine metric
            if 'margin' in query:
                metric = 'margin'
                metric_name = 'Gross Margin'
                top_oems = sorted(
                    [(k, v['total_margin']) for k, v in self.oem_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:  # Default to revenue
                metric = 'revenue'
                metric_name = 'Revenue'
                top_oems = sorted(
                    [(k, v['total_revenue']) for k, v in self.oem_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

            # Build response
            result = f"🏆 **Top 10 OEMs by {metric_name}**\n\n"
            for i, (oem, value) in enumerate(top_oems, 1):
                result += f"{i}. {oem}: {format_in_crores(value)}\n"

            # Add regional breakdown if requested
            if 'region' in query:
                result += "\n🌍 **Regional Breakdown for Top OEMs:**\n"
                for oem, _ in top_oems[:3]:  # Show top 3 for brevity
                    regional_data = self.oem_stats[oem].get('regional_revenue' if metric == 'revenue' else 'regional_margin', {})
                    if regional_data:
                        result += f"\n🏭 **{oem}**\n"
                        for region, value in sorted(regional_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {region}: {format_in_crores(value)}\n"

            # Add vertical breakdown if requested
            if 'vertical' in query or 'account' in query:
                result += "\n🏢 **Vertical Breakdown for Top OEMs:**\n"
                for oem, _ in top_oems[:3]:  # Show top 3 for brevity
                    vertical_data = self.oem_stats[oem].get('vertical_revenue' if metric == 'revenue' else 'vertical_margin', {})
                    if vertical_data:
                        result += f"\n🏭 **{oem}**\n"
                        for vertical, value in sorted(vertical_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {vertical}: {format_in_crores(value)}\n"

            return result
        except Exception as e:
            print(f"Error in top OEMs handling: {e}")
            return None
    
    def calculate_oem_growth_metrics(self, oem_data, oem_name):
        """Calculate growth metrics specific to OEM performance"""
        try:
            metrics = {}
            
            # Quarterly growth if we have quarterly data
            if 'Quarter' in oem_data.columns:
                quarterly_data = oem_data.groupby('Quarter').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_index()
                
                if len(quarterly_data) >= 2:
                    quarters = sorted(quarterly_data.index)
                    current_quarter = quarters[-1]
                    prev_quarter = quarters[-2]
                    
                    current_rev = quarterly_data.loc[current_quarter, 'TL Base Value']
                    prev_rev = quarterly_data.loc[prev_quarter, 'TL Base Value']
                    qoq_growth = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                    
                    metrics[f"Latest QoQ Growth"] = qoq_growth
            
            # Yearly growth
            if 'Fiscal Year' in oem_data.columns:
                yearly_data = oem_data.groupby('Fiscal Year').agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).sort_index()
                
                if len(yearly_data) >= 2:
                    years = sorted(yearly_data.index)
                    current_year = years[-1]
                    prev_year = years[-2]
                    
                    current_rev = yearly_data.loc[current_year, 'TL Base Value']
                    prev_rev = yearly_data.loc[prev_year, 'TL Base Value']
                    yoy_growth = ((current_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
                    
                    metrics[f"Latest YoY Growth"] = yoy_growth
            
            # Average deal size and transaction frequency
            avg_deal_size = oem_data['TL Base Value'].mean()
            avg_margin_percent = (oem_data['Gross Margin Value'].sum() / oem_data['TL Base Value'].sum() * 100) if oem_data['TL Base Value'].sum() > 0 else 0
            
            metrics["Average Deal Size"] = f"{format_in_crores(avg_deal_size)}"
            metrics["Overall Margin %"] = f"{avg_margin_percent:.1f}%"
            
            # Market share among all OEMs
            total_market_revenue = self.df['TL Base Value'].sum()
            oem_revenue = oem_data['TL Base Value'].sum()
            market_share = (oem_revenue / total_market_revenue * 100) if total_market_revenue > 0 else 0
            
            metrics["Market Share"] = f"{market_share:.1f}%"
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating OEM growth metrics: {e}")
            return {}
        
    def handle_vertical_query(self, query):
        """Handle vertical specific queries with comprehensive multi-year and regional analysis using interactive HTML tables"""
        import re
        import pandas as pd
        
        try:
            print(f"DEBUG: Vertical handler called with: {query}")
            
            # Check if Vertical column exists
            vertical_column = 'Vertical'
            if vertical_column not in self.df.columns:
                print("DEBUG: No Vertical column found")
                return "❌ Vertical data not available in this dataset"
            
            print(f"DEBUG: Available columns: {list(self.df.columns)}")
            
            # Extract vertical name with improved matching strategy
            vertical_name = None
            query_lower = query.lower()
            
            # Get all unique verticals and sort by length (longest first) to prioritize specific matches
            verticals = sorted(self.df['Vertical'].dropna().unique(), key=len, reverse=True)
            print(f"DEBUG: Available verticals: {list(verticals)}")
            
            # Try multiple regex patterns for vertical extraction
            patterns = [
                r'vertical\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'vertical\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+vertical\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|performance).*?(?:for|of)\s+([^,\n]+?)(?:\s+vertical|$)'
            ]
            
            vertical_match = None
            for pattern in patterns:
                vertical_match = re.search(pattern, query_lower)
                if vertical_match:
                    print(f"DEBUG: Vertical extracted with pattern: {pattern}")
                    break
            
            # If regex match found, use it; otherwise try existing logic
            if vertical_match:
                requested_vertical = vertical_match.group(1).strip()
                print(f"DEBUG: Extracted vertical from regex: '{requested_vertical}'")
                
                # Find exact match (case insensitive)
                for vertical in verticals:
                    if str(vertical).lower().strip() == requested_vertical.lower().strip():
                        vertical_name = vertical
                        print(f"DEBUG: Exact match found: {vertical_name}")
                        break
                
                # Try partial match if exact fails
                if not vertical_name:
                    for vertical in verticals:
                        if requested_vertical.lower().strip() in str(vertical).lower().strip():
                            vertical_name = vertical
                            print(f"DEBUG: Partial match found: {vertical_name}")
                            break
            
            # Fallback to original matching logic if regex didn't work
            if not vertical_name:
                print("DEBUG: Using original matching logic")
                # Try to find the best match, prioritizing longer/more specific vertical names
                for vertical in verticals:
                    vertical_lower = str(vertical).lower()
                    
                    # Skip empty or very short ambiguous verticals initially
                    if len(vertical_lower.strip()) <= 1:
                        continue
                        
                    # For verticals with special characters, use exact phrase matching
                    if any(char in vertical_lower for char in ['-', '_', '/', '&', '+', '.']):
                        # Look for the exact vertical name as a phrase (with word boundaries where appropriate)
                        if vertical_lower in query_lower:
                            # Additional check: make sure it's not part of a larger word
                            # Find the position of the match
                            pos = query_lower.find(vertical_lower)
                            if pos != -1:
                                # Check characters before and after the match
                                before_char = query_lower[pos-1] if pos > 0 else ' '
                                after_char = query_lower[pos+len(vertical_lower)] if pos+len(vertical_lower) < len(query_lower) else ' '
                                
                                # Consider it a match if surrounded by non-alphanumeric characters
                                if not (before_char.isalnum() or after_char.isalnum()):
                                    vertical_name = vertical
                                    break
                    else:
                        # For regular vertical names, use word boundary matching
                        if re.search(rf'\b{re.escape(vertical_lower)}\b', query_lower):
                            vertical_name = vertical
                            break
                
                # If no match found yet, try the very short/ambiguous verticals (like single characters)
                if not vertical_name:
                    for vertical in verticals:
                        vertical_lower = str(vertical).lower().strip()
                        if len(vertical_lower) <= 1:
                            # For single character verticals, be very strict
                            if vertical_lower in query_lower:
                                # Make sure it's truly isolated (surrounded by spaces or punctuation)
                                pattern = rf'(?<!\w){re.escape(vertical_lower)}(?!\w)'
                                if re.search(pattern, query_lower):
                                    vertical_name = vertical
                                    break
            
            if not vertical_name:
                print("DEBUG: No vertical match found")
                available_verticals = ', '.join(sorted(self.df['Vertical'].dropna().unique()))
                return f"❌ Please specify a valid vertical account name. Available verticals: {available_verticals}"
            
            print(f"DEBUG: Final matched vertical: '{vertical_name}'")
            
            # Get all data for this vertical
            vertical_data = self.df[self.df[vertical_column] == vertical_name]
            available_years = sorted(vertical_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for vertical {vertical_name}"
            
            print(f"DEBUG: Available years for {vertical_name}: {available_years}")
            
            # Check if end customer data is available
            customer_column = None
            possible_customer_columns = ['End Customer Name', 'End Customer', 'Customer Name', 'Customer', 'End_Customer_Name']
            for col in possible_customer_columns:
                if col in self.df.columns:
                    customer_column = col
                    print(f"DEBUG: Found customer column: {customer_column}")
                    break
            
            if not customer_column:
                print(f"DEBUG: No customer column found. Available columns: {list(self.df.columns)}")
                # Still continue but without customer data
            
            # Handle simple transaction count queries (maintain backward compatibility)
            if 'transaction count' in query_lower and 'growth' not in query_lower and 'performance' not in query_lower:
                year = None
                year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
                if year_match:
                    year = 2000 + int(year_match.group(2) if year_match.group(2) else year_match.group(1))
                
                if year:
                    year_data = vertical_data[vertical_data['Year_Start'] == year]
                    transaction_count = len(year_data)
                    return f"📊 Vertical Account: {vertical_name} Transactions in {year}: {transaction_count:,}"
                else:
                    transaction_count = len(vertical_data)
                    return f"📊 Vertical Account: {vertical_name} Total Transactions: {transaction_count:,}"
            
            # Build comprehensive output with interactive HTML tables
            output_text = f"## PERFORMANCE FOR {vertical_name.upper()} VERTICAL\n\n"
            
            # Year-wise performance summary table
            yearly_summary_data = []
            yearly_customer_data = {}  # Store customer data for each year
            
            for year in available_years:
                year_data = vertical_data[vertical_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = vertical_data[vertical_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(year_data)
                
                # Get top 5 end customers for this year
                year_customers = []
                if customer_column and customer_column in year_data.columns:
                    print(f"DEBUG: Processing customers for year {year}")
                    customer_stats = year_data[year_data[customer_column].notna()].groupby(customer_column).agg(
                        Revenue=('TL Base Value', 'sum'),
                        Margin=('Gross Margin Value', 'sum'),
                        Transactions=('TL Base Value', 'count')
                    ).reset_index().sort_values('Revenue', ascending=False).head(5)
                    
                    print(f"DEBUG: Found {len(customer_stats)} customers for year {year}")
                    
                    for _, customer_row in customer_stats.iterrows():
                        customer_gm_percent = (customer_row['Margin'] / customer_row['Revenue'] * 100) if customer_row['Revenue'] > 0 else 0
                        year_customers.append({
                            'name': str(customer_row[customer_column])[:25],  # Truncate long names
                            'revenue': f"₹{customer_row['Revenue']/10000000:.2f}Cr",
                            'margin': f"₹{customer_row['Margin']/10000000:.2f}Cr",
                            'gm_percent': f"{customer_gm_percent:.1f}%",
                            'transactions': f"{int(customer_row['Transactions']):,}"
                        })
                        print(f"DEBUG: Added customer: {customer_row[customer_column]}")
                else:
                    print(f"DEBUG: No customer column or no data for year {year}")
                
                yearly_customer_data[year] = year_customers
                print(f"DEBUG: Year {year} has {len(year_customers)} customers")
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                txn_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    prev_count = len(prev_year_data)
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                    
                    if prev_count > 0:
                        txn_growth = ((transaction_count - prev_count) / prev_count * 100)
                        txn_growth_str = f"{txn_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'Transactions': f"{transaction_count:,}",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str,
                    'Txn Growth': txn_growth_str,
                    'year_key': year  # For linking with customer data
                })
            
            # Create interactive yearly summary table
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_interactive_html_table(
                    yearly_df,
                    yearly_customer_data,
                    table_id=f"{vertical_name.lower().replace(' ', '_')}_yearly_summary",
                    title=f"{vertical_name} Vertical - Yearly Performance",
                    table_type="yearly",
                    detail_type="customers"
                )
                output_text += yearly_table_html + "\n\n"
            
            # Regional Analysis Section
            region_column = 'Region'
            if region_column in vertical_data.columns:
                output_text += "### REGIONAL PERFORMANCE\n\n"
                
                # Regional summary for each year
                for year in available_years:
                    year_data = vertical_data[vertical_data['Year_Start'] == year]
                    prev_year_data = vertical_data[vertical_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty regions
                    year_filtered = year_data[year_data[region_column].notna() & (year_data[region_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats by region
                    current_stats = year_filtered.groupby(region_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum'),
                        Txn_Current=('TL Base Value', 'count')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Get customer data for each region
                    regional_customer_data = {}
                    for _, region_row in current_stats.iterrows():
                        region_name = region_row[region_column]
                        region_data = year_filtered[year_filtered[region_column] == region_name]
                        
                        region_customers = []
                        if customer_column and customer_column in region_data.columns:
                            print(f"DEBUG: Processing customers for region {region_name} in year {year}")
                            customer_stats = region_data[region_data[customer_column].notna()].groupby(customer_column).agg(
                                Revenue=('TL Base Value', 'sum'),
                                Margin=('Gross Margin Value', 'sum'),
                                Transactions=('TL Base Value', 'count')
                            ).reset_index().sort_values('Revenue', ascending=False).head(5)
                            
                            print(f"DEBUG: Found {len(customer_stats)} customers for region {region_name}")
                            
                            for _, customer_row in customer_stats.iterrows():
                                customer_gm_percent = (customer_row['Margin'] / customer_row['Revenue'] * 100) if customer_row['Revenue'] > 0 else 0
                                region_customers.append({
                                    'name': str(customer_row[customer_column])[:25],
                                    'revenue': f"₹{customer_row['Revenue']/10000000:.2f}Cr",
                                    'margin': f"₹{customer_row['Margin']/10000000:.2f}Cr",
                                    'gm_percent': f"{customer_gm_percent:.1f}%",
                                    'transactions': f"{int(customer_row['Transactions']):,}"
                                })
                        else:
                            print(f"DEBUG: No customer column or no data for region {region_name}")
                        
                        regional_customer_data[region_name] = region_customers
                        print(f"DEBUG: Region {region_name} has {len(region_customers)} customers")
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and region_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[region_column].notna() & (prev_year_data[region_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(region_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum'),
                                Txn_Prev=('TL Base Value', 'count')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=region_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        merged_stats['Txn_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        region_name = str(row[region_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        txn_prev_val = float(row['Txn_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        txn_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        if txn_prev_val > 0:
                            txn_growth = (row['Txn_Current'] - txn_prev_val) / txn_prev_val * 100
                            txn_growth_str = f"{txn_growth:+.1f}%"
                        elif row['Txn_Current'] > 0:
                            txn_growth_str = "New"
                        
                        table_data.append({
                            'Region': region_name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Transactions': f"{int(row['TL_Current']):,}",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str,
                            'Txn Growth': txn_growth_str,
                            'region_key': str(row[region_column])  # For linking with customer data
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        output_text += f"**{year_str}:**\n\n"
                        
                        # Create DataFrame and generate interactive HTML table
                        region_df = pd.DataFrame(table_data)
                        table_html = self._generate_interactive_html_table(
                            region_df,
                            regional_customer_data,
                            table_id=f"{vertical_name.lower().replace(' ', '_')}_regional_{year}",
                            title=f"Regional Performance - {year_str}",
                            table_type="regional",
                            detail_type="customers"
                        )
                        output_text += table_html + "\n\n"
            else:
                output_text += "### REGIONAL PERFORMANCE\n❌ Region column not found in data\n\n"
            
            print(f"DEBUG: Generated comprehensive interactive HTML table report for {vertical_name}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing vertical query: {str(e)}"
    
    def handle_end_customer_query(self, query):
        """Handle end customer-related queries with comprehensive multi-year and regional analysis using interactive HTML tables"""
        try:
            print(f"DEBUG: End Customer handler called with: {query}")
            
            # DEBUG: Print all available columns
            print(f"DEBUG: Available columns in dataframe: {list(self.df.columns)}")
            print(f"DEBUG: Looking for customer-related columns...")
            customer_cols = [col for col in self.df.columns if 'customer' in col.lower() or 'client' in col.lower()]
            print(f"DEBUG: Found customer-related columns: {customer_cols}")
            
            # Extract end customer name from query - improved regex patterns
            query_lower = query.lower()
            customer_match = None
            
            # Try multiple regex patterns for end customer extraction - IMPROVED PATTERNS
            patterns = [
                r'(?:end customer|customer|client)\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:for|of)\s+(?:end customer|customer|client)\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|display|get|performance).*?(?:for|of)\s+(?:end customer|customer|client)?\s*([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:end customer|customer|client)\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'(?:show|performance|display).*?(?:for|of)\s+([^,\n]+?)(?:\s+(?:end customer|customer|client)|$)'
            ]
            
            for pattern in patterns:
                customer_match = re.search(pattern, query_lower)
                if customer_match:
                    print(f"DEBUG: End Customer extracted with pattern: {pattern}")
                    print(f"DEBUG: Matched groups: {customer_match.groups()}")
                    break
            
            # Find the correct customer column - IMPROVED LOGIC
            customer_column = None
            possible_customer_columns = ['End Customer Name', 'End Customer', 'Customer Name', 'Customer', 'End_Customer_Name', 'end customer name', 'end customer']
            
            for col in possible_customer_columns:
                if col in self.df.columns:
                    customer_column = col
                    print(f"DEBUG: Found customer column: {customer_column}")
                    break
            
            if not customer_column:
                print(f"DEBUG: No customer column found. Available columns: {list(self.df.columns)}")
                return f"❌ End Customer column not found in data. Available columns: {', '.join(list(self.df.columns)[:10])}"
            
            # If no regex match, try direct matching with available end customers
            if not customer_match:
                print("DEBUG: No regex match, trying direct end customer matching")
                if customer_column in self.df.columns:
                    available_customers = self.df[customer_column].dropna().unique()
                    matched_directly = None
                    for customer in available_customers:
                        if str(customer).lower() in query_lower:
                            matched_directly = customer
                            print(f"DEBUG: Direct match found: {customer}")
                            break
                    
                    # Create a simple object with group method if we found a direct match
                    if matched_directly:
                        class DirectMatch:
                            def __init__(self, value):
                                self.value = value
                            def group(self, index):
                                return self.value
                        customer_match = DirectMatch(matched_directly)
            
            if not customer_match:
                print("DEBUG: No end customer match found")
                if customer_column in self.df.columns:
                    available_customers = self.df[customer_column].dropna().unique()
                    return (f"❌ Please specify an end customer name.\n"
                            f"Available: {', '.join(map(str, available_customers[:5]))}")
                else:
                    return "❌ End Customer column not found in data"
            
            requested_customer = customer_match.group(1).strip()
            print(f"DEBUG: Extracted end customer: '{requested_customer}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_customer = None
            available_customers = self.df[customer_column].dropna().unique()
            
            print(f"DEBUG: Available end customers: {list(available_customers)[:10]}")
            
            # Try exact match first
            for customer in available_customers:
                if str(customer).lower().strip() == requested_customer.lower().strip():
                    matched_customer = customer
                    print(f"DEBUG: Exact match found: {matched_customer}")
                    break
            
            # Try partial match if exact fails
            if not matched_customer:
                for customer in available_customers:
                    if requested_customer.lower().strip() in str(customer).lower().strip():
                        matched_customer = customer
                        print(f"DEBUG: Partial match found: {matched_customer}")
                        break
            
            if not matched_customer:
                print(f"DEBUG: No match found for '{requested_customer}'")
                return (f"❌ End Customer '{requested_customer}' not found.\n"
                        f"Available: {', '.join(map(str, available_customers[:5]))}")
            
            # Get all data for this end customer
            customer_data = self.df[self.df[customer_column] == matched_customer]
            available_years = sorted(customer_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for end customer {matched_customer}"
            
            print(f"DEBUG: Available years for {matched_customer}: {available_years}")
            
            # Check if partner data is available
            partner_column = 'Partner'
            if partner_column not in self.df.columns:
                print(f"DEBUG: No partner column found. Available columns: {list(self.df.columns)}")
                return "❌ Partner column not found in data"
            
            # Build comprehensive output with interactive HTML tables
            output_text = f"## PERFORMANCE FOR {matched_customer.upper()} END CUSTOMER\n\n"
            
            # Year-wise performance summary table
            yearly_summary_data = []
            yearly_partner_data = {}  # Store partner data for each year
            
            for year in available_years:
                year_data = customer_data[customer_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = customer_data[customer_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(year_data)
                
                # Get top 5 partners for this year
                year_partners = []
                if partner_column in year_data.columns:
                    print(f"DEBUG: Processing partners for year {year}")
                    partner_stats = year_data[year_data[partner_column].notna()].groupby(partner_column).agg(
                        Revenue=('TL Base Value', 'sum'),
                        Margin=('Gross Margin Value', 'sum'),
                        Transactions=('TL Base Value', 'count')
                    ).reset_index().sort_values('Revenue', ascending=False).head(5)
                    
                    print(f"DEBUG: Found {len(partner_stats)} partners for year {year}")
                    
                    for _, partner_row in partner_stats.iterrows():
                        partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                        year_partners.append({
                            'name': str(partner_row[partner_column])[:25],  # Truncate long names
                            'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                            'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                            'gm_percent': f"{partner_gm_percent:.1f}%",
                            'transactions': f"{int(partner_row['Transactions']):,}"
                        })
                        print(f"DEBUG: Added partner: {partner_row[partner_column]}")
                else:
                    print(f"DEBUG: No partner column or no data for year {year}")
                
                yearly_partner_data[year] = year_partners
                print(f"DEBUG: Year {year} has {len(year_partners)} partners")
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                txn_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    prev_count = len(prev_year_data)
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                    
                    if prev_count > 0:
                        txn_growth = ((transaction_count - prev_count) / prev_count * 100)
                        txn_growth_str = f"{txn_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'Transactions': f"{transaction_count:,}",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str,
                    'Txn Growth': txn_growth_str,
                    'year_key': year  # For linking with partner data
                })
            
            # Create interactive yearly summary table
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_interactive_html_table(
                    yearly_df,
                    yearly_partner_data,
                    table_id=f"{matched_customer.lower().replace(' ', '_')}_yearly_summary",
                    title=f"{matched_customer} End Customer - Yearly Performance",
                    table_type="yearly",
                    detail_type="partners"
                )
                output_text += yearly_table_html + "\n\n"
            
            # Regional Analysis Section
            region_column = 'Region'
            if region_column in customer_data.columns:
                output_text += "### REGIONAL PERFORMANCE\n\n"
                
                # Regional summary for each year
                for year in available_years:
                    year_data = customer_data[customer_data['Year_Start'] == year]
                    prev_year_data = customer_data[customer_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty regions
                    year_filtered = year_data[year_data[region_column].notna() & (year_data[region_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats by region
                    current_stats = year_filtered.groupby(region_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum'),
                        Txn_Current=('TL Base Value', 'count')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Get partner data for each region
                    regional_partner_data = {}
                    for _, region_row in current_stats.iterrows():
                        region_name = region_row[region_column]
                        region_data = year_filtered[year_filtered[region_column] == region_name]
                        
                        region_partners = []
                        if partner_column in region_data.columns:
                            print(f"DEBUG: Processing partners for region {region_name} in year {year}")
                            partner_stats = region_data[region_data[partner_column].notna()].groupby(partner_column).agg(
                                Revenue=('TL Base Value', 'sum'),
                                Margin=('Gross Margin Value', 'sum'),
                                Transactions=('TL Base Value', 'count')
                            ).reset_index().sort_values('Revenue', ascending=False).head(5)
                            
                            print(f"DEBUG: Found {len(partner_stats)} partners for region {region_name}")
                            
                            for _, partner_row in partner_stats.iterrows():
                                partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                                region_partners.append({
                                    'name': str(partner_row[partner_column])[:25],
                                    'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                                    'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                                    'gm_percent': f"{partner_gm_percent:.1f}%",
                                    'transactions': f"{int(partner_row['Transactions']):,}"
                                })
                        else:
                            print(f"DEBUG: No partner column or no data for region {region_name}")
                        
                        regional_partner_data[region_name] = region_partners
                        print(f"DEBUG: Region {region_name} has {len(region_partners)} partners")
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and region_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[region_column].notna() & (prev_year_data[region_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(region_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum'),
                                Txn_Prev=('TL Base Value', 'count')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=region_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        merged_stats['Txn_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        region_name = str(row[region_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        txn_prev_val = float(row['Txn_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        txn_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        if txn_prev_val > 0:
                            txn_growth = (row['Txn_Current'] - txn_prev_val) / txn_prev_val * 100
                            txn_growth_str = f"{txn_growth:+.1f}%"
                        elif row['Txn_Current'] > 0:
                            txn_growth_str = "New"
                        
                        table_data.append({
                            'Region': region_name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Transactions': f"{int(row['Txn_Current']):,}",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str,
                            'Txn Growth': txn_growth_str,
                            'region_key': str(row[region_column])  # For linking with partner data
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        output_text += f"**{year_str}:**\n\n"
                        
                        # Create DataFrame and generate interactive HTML table
                        region_df = pd.DataFrame(table_data)
                        table_html = self._generate_interactive_html_table(
                            region_df,
                            regional_partner_data,
                            table_id=f"{matched_customer.lower().replace(' ', '_')}_regional_{year}",
                            title=f"Regional Performance - {year_str}",
                            table_type="regional",
                            detail_type="partners"
                        )
                        output_text += table_html + "\n\n"
            else:
                output_text += "### REGIONAL PERFORMANCE\n❌ Region column not found in data\n\n"
            
            print(f"DEBUG: Generated comprehensive interactive HTML table report for {matched_customer}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing end customer query: {str(e)}"

    def handle_customer_query(self, query):
        """Handle detailed end customer performance queries"""
        try:
            # Extract customer name (flexible matching)
            customer_name = None
            for cust in self.df['End Customer'].dropna().unique():
                if str(cust).lower() in query.lower():
                    customer_name = cust
                    break
            
            if not customer_name:
                return "❌ Please specify a valid customer name"

            # Extract year if specified
            year = None
            year_match = re.search(r'(?:20)?(\d{2})', query)  # Matches 2023 or 23
            if year_match:
                year = 2000 + int(year_match.group(1))

            # Get performance data
            performance = self.processor.get_customer_performance(customer_name, year)
            if not performance:
                return f"❌ No data found for {customer_name} in {year}" if year else f"❌ No data found for {customer_name}"

            # Determine query type
            if 'revenue' in query.lower():
                return f"💰 End Customer: {customer_name} Revenue (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(performance['total_revenue'])}"
            
            elif 'margin' in query.lower():
                return f"💹 End Customer: {customer_name} Gross Margin (FY{str(year)[2:] if year else 'All Time'}): {format_in_crores(performance['total_margin'])} (GM%: {performance['gm_percent']:.1f}%)"
            
            elif 'transaction' in query.lower() or 'count' in query.lower():
                return f"📊 End Customer: {customer_name} Transactions (FY{str(year)[2:] if year else 'All Time'}): {performance['transaction_count']:,}"
            
            elif 'growth' in query.lower() and year:
                # Calculate growth from previous year
                prev_year = year - 1
                current_perf = performance
                prev_perf = self.processor.get_customer_performance(customer_name, prev_year)
                
                if not prev_perf:
                    return f"❌ Cannot calculate growth - no data for {prev_year}"
                
                rev_growth = ((current_perf['total_revenue'] - prev_perf['total_revenue']) / 
                            prev_perf['total_revenue'] * 100) if prev_perf['total_revenue'] > 0 else 0
                margin_growth = ((current_perf['total_margin'] - prev_perf['total_margin']) / 
                            prev_perf['total_margin'] * 100) if prev_perf['total_margin'] > 0 else 0
                
                return (f"📈 End Customer: {customer_name} Growth (FY{prev_year}→FY{year}):\n"
                    f"   • Revenue: {rev_growth:+.1f}%\n"
                    f"   • Gross Margin: {margin_growth:+.1f}%")
            
            else:
                # Default comprehensive response
                year_str = f" (FY{str(year)[2:]})" if year else ""
                return (f"📊 End Customer: {customer_name} Performance{year_str}:\n"
                    f"   • Revenue: {format_in_crores(performance['total_revenue'])}\n"
                    f"   • Gross Margin: {format_in_crores(performance['total_margin'])} (GM%: {performance['gm_percent']:.1f}%)\n"
                    f"   • Transactions: {performance['transaction_count']:,}\n"
                    f"   • First Transaction: {performance['first_transaction'].strftime('%d-%b-%Y')}\n"
                    f"   • Last Transaction: {performance['last_transaction'].strftime('%d-%b-%Y')}")

        except Exception as e:
            return f"❌ Error processing customer query: {str(e)}"

    def handle_top_partners(self, query):
        """Handle queries about top partners"""
        try:
            # Determine metric
            if 'margin' in query:
                metric = 'margin'
                metric_name = 'Gross Margin'
                top_partners = sorted(
                    [(k, v['total_margin']) for k, v in self.partner_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:  # Default to revenue
                metric = 'revenue'
                metric_name = 'Revenue'
                top_partners = sorted(
                    [(k, v['total_revenue']) for k, v in self.partner_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

            # Build response
            result = f"🏆 **Top 10 Partners by {metric_name}**\n\n"
            for i, (partner, value) in enumerate(top_partners, 1):
                result += f"{i}. {partner}: {format_in_crores(value)}\n"

            # Add regional breakdown if requested
            if 'region' in query:
                result += "\n🌍 **Regional Breakdown for Top Partners:**\n"
                for partner, _ in top_partners[:3]:  # Show top 3 for brevity
                    regional_data = self.partner_stats[partner].get('regional_revenue' if metric == 'revenue' else 'regional_margin', {})
                    if regional_data:
                        result += f"\n🤝 **{partner}**\n"
                        for region, value in sorted(regional_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {region}: {format_in_crores(value)}\n"

            # Add vertical breakdown if requested
            if 'vertical' in query or 'account' in query:
                result += "\n🏢 **Vertical Breakdown for Top Partners:**\n"
                for partner, _ in top_partners[:3]:  # Show top 3 for brevity
                    vertical_data = self.partner_stats[partner].get('vertical_revenue' if metric == 'revenue' else 'vertical_margin', {})
                    if vertical_data:
                        result += f"\n🤝 **{partner}**\n"
                        for vertical, value in sorted(vertical_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {vertical}: {format_in_crores(value)}\n"

            return result

        except Exception as e:
            print(f"Error in top partners handling: {e}")
            return None

    def handle_top_oems(self, query):
        """Handle queries about top OEMs"""
        try:
            # Determine metric
            if 'margin' in query:
                metric = 'margin'
                metric_name = 'Gross Margin'
                top_oems = sorted(
                    [(k, v['total_margin']) for k, v in self.oem_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:  # Default to revenue
                metric = 'revenue'
                metric_name = 'Revenue'
                top_oems = sorted(
                    [(k, v['total_revenue']) for k, v in self.oem_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

            # Build response
            result = f"🏆 **Top 10 OEMs by {metric_name}**\n\n"
            for i, (oem, value) in enumerate(top_oems, 1):
                result += f"{i}. {oem}: {format_in_crores(value)}\n"

            # Add regional breakdown if requested
            if 'region' in query:
                result += "\n🌍 **Regional Breakdown for Top OEMs:**\n"
                for oem, _ in top_oems[:3]:  # Show top 3 for brevity
                    regional_data = self.oem_stats[oem].get('regional_revenue' if metric == 'revenue' else 'regional_margin', {})
                    if regional_data:
                        result += f"\n🏭 **{oem}**\n"
                        for region, value in sorted(regional_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {region}: {format_in_crores(value)}\n"

            # Add vertical breakdown if requested
            if 'vertical' in query or 'account' in query:
                result += "\n🏢 **Vertical Breakdown for Top OEMs:**\n"
                for oem, _ in top_oems[:3]:  # Show top 3 for brevity
                    vertical_data = self.oem_stats[oem].get('vertical_revenue' if metric == 'revenue' else 'vertical_margin', {})
                    if vertical_data:
                        result += f"\n🏭 **{oem}**\n"
                        for vertical, value in sorted(vertical_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {vertical}: {format_in_crores(value)}\n"

            return result

        except Exception as e:
            print(f"Error in top OEMs handling: {e}")
            return None

    def handle_top_verticals(self, query):
        """Handle queries about top verticals"""
        try:
            # Determine metric - default to revenue if not specified
            if 'margin' in query:
                metric = 'margin'
                metric_name = 'Gross Margin'
                top_verticals = sorted(
                    [(k, v['total_margin']) for k, v in self.vertical_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:  # Default to revenue
                metric = 'revenue'
                metric_name = 'Revenue'
                top_verticals = sorted(
                    [(k, v['total_revenue']) for k, v in self.vertical_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

            # Build response
            if not top_verticals:
                return "❌ No vertical data available"

            result = f"🏆 **Top 10 Verticals by {metric_name}**\n\n"
            for i, (vertical, value) in enumerate(top_verticals, 1):
                result += f"{i}. {vertical}: {format_in_crores(value)}\n"

            # Add regional breakdown if requested
            if 'region' in query:
                result += "\n🌍 **Regional Breakdown for Top Verticals:**\n"
                for vertical, _ in top_verticals[:3]:  # Show top 3 for brevity
                    regional_data = self.vertical_stats[vertical].get('regional_revenue' if metric == 'revenue' else 'regional_margin', {})
                    if regional_data:
                        result += f"\n🏢 **{vertical}**\n"
                        for region, value in sorted(regional_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {region}: {format_in_crores(value)}\n"

            # Add partner breakdown if requested
            if 'partner' in query:
                result += "\n🤝 **Partner Breakdown for Top Verticals:**\n"
                for vertical, _ in top_verticals[:3]:  # Show top 3 for brevity
                    partner_data = self.vertical_stats[vertical].get('partner_revenue' if metric == 'revenue' else 'partner_margin', {})
                    if partner_data:
                        result += f"\n🏢 **{vertical}**\n"
                        for partner, value in sorted(partner_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {partner}: {format_in_crores(value)}\n"

            return result

        except Exception as e:
            print(f"Error in top verticals handling: {e}")
            return f"❌ Error retrieving top verticals: {e}"

    def handle_top_customers(self, query):
        """Handle queries about top end customers"""
        try:
            # Determine metric
            if 'margin' in query:
                metric = 'margin'
                metric_name = 'Gross Margin'
                top_customers = sorted(
                    [(k, v['total_margin']) for k, v in self.customer_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            else:  # Default to revenue
                metric = 'revenue'
                metric_name = 'Revenue'
                top_customers = sorted(
                    [(k, v['total_revenue']) for k, v in self.customer_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

            # Build response
            result = f"🏆 **Top 10 End Customers by {metric_name}**\n\n"
            for i, (customer, value) in enumerate(top_customers, 1):
                result += f"{i}. {customer}: {format_in_crores(value)}\n"

            # Add regional breakdown if requested
            if 'region' in query:
                result += "\n🌍 **Regional Breakdown for Top Customers:**\n"
                for customer, _ in top_customers[:3]:  # Show top 3 for brevity
                    regional_data = self.customer_stats[customer].get('regional_revenue' if metric == 'revenue' else 'regional_margin', {})
                    if regional_data:
                        result += f"\n👥 **{customer}**\n"
                        for region, value in sorted(regional_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {region}: {format_in_crores(value)}\n"

            # Add partner breakdown if requested
            if 'partner' in query:
                result += "\n🤝 **Partner Breakdown for Top Customers:**\n"
                for customer, _ in top_customers[:3]:  # Show top 3 for brevity
                    partner_data = self.customer_stats[customer].get('partner_revenue' if metric == 'revenue' else 'partner_margin', {})
                    if partner_data:
                        result += f"\n👥 **{customer}**\n"
                        for partner, value in sorted(partner_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {partner}: {format_in_crores(value)}\n"

            # Add vertical breakdown if requested
            if 'vertical' in query or 'account' in query:
                result += "\n🏢 **Vertical Breakdown for Top Customers:**\n"
                for customer, _ in top_customers[:3]:  # Show top 3 for brevity
                    vertical_data = self.customer_stats[customer].get('vertical_revenue' if metric == 'revenue' else 'vertical_margin', {})
                    if vertical_data:
                        result += f"\n👥 **{customer}**\n"
                        for vertical, value in sorted(vertical_data.items(), key=lambda x: x[1], reverse=True)[:3]:
                            result += f"   • {vertical}: {format_in_crores(value)}\n"

            return result

        except Exception as e:
            print(f"Error in top customers handling: {e}")
            return None

    def handle_comparison_query(self, query):
        """Handle year-to-year comparison queries"""
        try:
            # Check if it's a comparison query
            comparison_keywords = ['compare', 'comparison', 'vs', 'versus', 'year over year', 'yoy', 'growth', 'change']
            if not any(keyword in query.lower() for keyword in comparison_keywords):
                return None

            # Add regional growth comparison
            if 'region' in query.lower():
                region = None
                # Find the region mentioned in the query
                for r in self.df['Region'].unique():
                    if r.lower() in query.lower():
                        region = r
                        break
                
                if region and 'comparisons' in self.yearly_stats:
                    region_growth = {}
                    for year_pair, comp_data in self.yearly_stats['comparisons'].items():
                        if 'region_comparison' in comp_data and region in comp_data['region_comparison']:
                            region_data = comp_data['region_comparison'][region]
                            if 'growth' in region_data:
                                region_growth[year_pair] = region_data['growth']
                    
                    if region_growth:
                        result = f"📈 **Growth in {region}:**\n"
                        for years, growth in sorted(region_growth.items()):
                            year_display = years.replace('_to_', ' to ')
                            result += f"   • {year_display}: {growth:+.1f}%\n"
                        return result

            # Extract specific years if mentioned
            years = []
            for year in self.yearly_stats.keys():
                if year != 'comparisons' and str(year) in query:
                    years.append(year)

            # If no specific years mentioned, use latest comparison
            if not years and 'comparisons' in self.yearly_stats:
                comparisons = self.yearly_stats['comparisons']
                if comparisons:
                    latest_comparison = list(comparisons.keys())[-1]
                    return self.format_comparison_result(latest_comparison, query)

            # If two years mentioned, compare them
            if len(years) == 2:
                year1, year2 = sorted(years)
                comparison_key = f'{year1}_to_{year2}'
                if comparison_key in self.yearly_stats.get('comparisons', {}):
                    return self.format_comparison_result(comparison_key, query)

            # If one year mentioned, compare with previous year
            if len(years) == 1:
                target_year = years[0]
                available_years = sorted([y for y in self.yearly_stats.keys() if y != 'comparisons'])
                if target_year in available_years:
                    year_index = available_years.index(target_year)
                    if year_index > 0:
                        prev_year = available_years[year_index - 1]
                        comparison_key = f'{prev_year}_to_{target_year}'
                        if comparison_key in self.yearly_stats.get('comparisons', {}):
                            return self.format_comparison_result(comparison_key, query)

            # Handle channel growth comparison
            if 'channel' in query.lower():
                channel = None
                # Find the channel mentioned in the query
                channels = self.stats.get('channel_values', [])
                for c in channels:
                    if c.lower() in query.lower():
                        channel = c
                        break
                
                if channel and 'comparisons' in self.yearly_stats:
                    channel_growth = {}
                    for year_pair, comp_data in self.yearly_stats['comparisons'].items():
                        if 'channel_comparison' in comp_data and channel in comp_data['channel_comparison']:
                            channel_data = comp_data['channel_comparison'][channel]
                            if 'growth' in channel_data:
                                channel_growth[year_pair] = channel_data['growth']
                    
                    if channel_growth:
                        result = f"📈 **Growth in {channel} Channel:**\n"
                        for years, growth in sorted(channel_growth.items()):
                            year_display = years.replace('_to_', ' to ')
                            result += f"   • {year_display}: {growth:+.1f}%\n"
                        return result

            # Handle vertical growth comparison
            if 'vertical' in query.lower():
                vertical = None
                # Find the vertical mentioned in the query
                verticals = self.stats.get('vertical_values', [])
                for v in verticals:
                    if v.lower() in query.lower():
                        vertical = v
                        break
                
                if vertical and 'comparisons' in self.yearly_stats:
                    vertical_growth = {}
                    for year_pair, comp_data in self.yearly_stats['comparisons'].items():
                        if 'vertical_comparison' in comp_data and vertical in comp_data['vertical_comparison']:
                            vertical_data = comp_data['vertical_comparison'][vertical]
                            if 'growth' in vertical_data:
                                vertical_growth[year_pair] = vertical_data['growth']
                    
                    if vertical_growth:
                        result = f"📈 **Growth in {vertical} Vertical:**\n"
                        for years, growth in sorted(vertical_growth.items()):
                            year_display = years.replace('_to_', ' to ')
                            result += f"   • {year_display}: {growth:+.1f}%\n"
                        return result

            # Handle partner growth comparison
            if 'partner' in query.lower():
                partner = None
                # Find the partner mentioned in the query
                if hasattr(self, 'partner_stats'):
                    partners = list(self.partner_stats.keys())
                    for p in partners:
                        if p.lower() in query.lower():
                            partner = p
                            break
                
                if partner and 'comparisons' in self.yearly_stats:
                    partner_growth = {}
                    for year_pair, comp_data in self.yearly_stats['comparisons'].items():
                        if 'partner_comparison' in comp_data and partner in comp_data['partner_comparison']:
                            partner_data = comp_data['partner_comparison'][partner]
                            if 'growth' in partner_data:
                                partner_growth[year_pair] = partner_data['growth']
                    
                    if partner_growth:
                        result = f"📈 **Growth for Partner {partner}:**\n"
                        for years, growth in sorted(partner_growth.items()):
                            year_display = years.replace('_to_', ' to ')
                            result += f"   • {year_display}: {growth:+.1f}%\n"
                        return result

            # Handle customer growth comparison
            if 'customer' in query.lower():
                customer = None
                # Find the customer mentioned in the query
                if hasattr(self, 'customer_stats'):
                    customers = list(self.customer_stats.keys())
                    for c in customers:
                        if c.lower() in query.lower():
                            customer = c
                            break
                
                if customer and 'comparisons' in self.yearly_stats:
                    customer_growth = {}
                    for year_pair, comp_data in self.yearly_stats['comparisons'].items():
                        if 'customer_comparison' in comp_data and customer in comp_data['customer_comparison']:
                            customer_data = comp_data['customer_comparison'][customer]
                            if 'growth' in customer_data:
                                customer_growth[year_pair] = customer_data['growth']
                    
                    if customer_growth:
                        result = f"📈 **Growth for Customer {customer}:**\n"
                        for years, growth in sorted(customer_growth.items()):
                            year_display = years.replace('_to_', ' to ')
                            result += f"   • {year_display}: {growth:+.1f}%\n"
                        return result

            # General comparison query
            return self.handle_general_comparison(query)

        except Exception as e:
            print(f"Error in comparison query handling: {e}")
            return None

    def format_comparison_result(self, comparison_key, query):
        """Format comparison results based on query type"""
        try:
            comparison_data = self.yearly_stats['comparisons'][comparison_key]
            years = comparison_key.split('_to_')
            prev_year, current_year = years[0], years[1]

            # Determine what metric to focus on
            if 'revenue' in query or 'sales' in query:
                growth = comparison_data['revenue_growth']
                difference = comparison_data['revenue_difference']
                metric = "Revenue"
                symbol = "₹"
            elif 'margin' in query:
                growth = comparison_data['margin_growth']
                difference = comparison_data['margin_difference']
                metric = "Gross Margin"
                symbol = "₹"
            elif 'transaction' in query:
                growth = comparison_data['transaction_growth']
                difference = comparison_data['transaction_difference']
                metric = "Transactions"
                symbol = ""
            else:
                # Provide comprehensive comparison
                result = f"📊 **Year-to-Year Comparison ({prev_year} vs {current_year}):**\n\n"

                # Revenue comparison
                rev_growth = comparison_data['revenue_growth']
                rev_diff = comparison_data['revenue_difference']
                trend_emoji = "📈" if rev_growth > 0 else "📉" if rev_growth < 0 else "➡️"
                result += f"{trend_emoji} **Revenue Growth:** {rev_growth:+.1f}% ({format_in_crores(rev_diff)})\n"

                # Margin comparison
                margin_growth = comparison_data['margin_growth']
                margin_diff = comparison_data['margin_difference']
                trend_emoji = "📈" if margin_growth > 0 else "📉" if margin_growth < 0 else "➡️"
                result += f"{trend_emoji} **Gross Margin Growth:** {margin_growth:+.1f}% ({format_in_crores(margin_diff)})\n"

                # Transaction comparison
                trans_growth = comparison_data['transaction_growth']
                trans_diff = comparison_data['transaction_difference']
                trend_emoji = "📈" if trans_growth > 0 else "📉" if trans_growth < 0 else "➡️"
                result += f"{trend_emoji} **Transaction Growth:** {trans_growth:+.1f}% ({trans_diff:+,.0f})\n"

                # Add channel comparison if available
                if 'channel_comparison' in comparison_data:
                    result += "\n**Channel Performance Comparison:**\n"
                    for channel, data in comparison_data['channel_comparison'].items():
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {channel}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add region comparison if available
                if 'region_comparison' in comparison_data:
                    result += "\n**Regional Performance Comparison:**\n"
                    for region, data in comparison_data['region_comparison'].items():
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {region}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add partner comparison if available
                if 'partner_comparison' in comparison_data:
                    result += "\n**Partner Performance Comparison (Top 5):**\n"
                    top_partners = sorted(comparison_data['partner_comparison'].items(),
                                        key=lambda x: abs(x[1]['difference']),
                                        reverse=True)[:5]
                    for partner, data in top_partners:
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {partner}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add OEM comparison if available
                if 'oem_comparison' in comparison_data:
                    result += "\n**OEM Performance Comparison (Top 5):**\n"
                    top_oems = sorted(comparison_data['oem_comparison'].items(),
                                    key=lambda x: abs(x[1]['difference']),
                                    reverse=True)[:5]
                    for oem, data in top_oems:
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {oem}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add vertical comparison if available
                if 'vertical_comparison' in comparison_data:
                    result += "\n**Vertical Performance Comparison (Top 5):**\n"
                    top_verticals = sorted(comparison_data['vertical_comparison'].items(),
                                        key=lambda x: abs(x[1]['difference']),
                                        reverse=True)[:5]
                    for vertical, data in top_verticals:
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {vertical}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add customer comparison if available
                if 'customer_comparison' in comparison_data:
                    result += "\n**Customer Performance Comparison (Top 5):**\n"
                    top_customers = sorted(comparison_data['customer_comparison'].items(),
                                        key=lambda x: abs(x[1]['difference']),
                                        reverse=True)[:5]
                    for customer, data in top_customers:
                        trend = "📈" if data['growth'] > 0 else "📉" if data['growth'] < 0 else "➡️"
                        result += f"   {trend} {customer}: {data['growth']:+.1f}% ({format_in_crores(data['difference'])})\n"

                # Add year-specific details
                prev_stats = self.yearly_stats[int(prev_year)]
                current_stats = self.yearly_stats[int(current_year)]

                result += f"\n**{prev_year} Performance:**\n"
                result += f"   • Revenue: {format_in_crores(prev_stats['total_revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(prev_stats['total_gross_margin'])}\n"
                result += f"   • Transactions: {prev_stats['total_transactions']:,}\n"

                result += f"\n**{current_year} Performance:**\n"
                result += f"   • Revenue: {format_in_crores(current_stats['total_revenue'])}\n"
                result += f"   • Gross Margin: {format_in_crores(current_stats['total_gross_margin'])}\n"
                result += f"   • Transactions: {current_stats['total_transactions']:,}\n"

                return result

            # Single metric comparison
            trend_emoji = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
            result = f"{trend_emoji} **{metric} Comparison ({prev_year} vs {current_year}):**\n"
            result += f"   • Growth Rate: {growth:+.1f}%\n"
            result += f"   • Difference: {format_in_crores(difference)}\n"

            return result

        except Exception as e:
            return f"❌ Error formatting comparison: {e}"

    def handle_general_comparison(self, query):
        """Handle general comparison queries"""
        try:
            if 'comparisons' not in self.yearly_stats or not self.yearly_stats['comparisons']:
                return "❌ No year-to-year comparison data available."

            # Show all available comparisons
            result = "📊 **All Year-to-Year Comparisons:**\n\n"

            for comparison_key, data in self.yearly_stats['comparisons'].items():
                years = comparison_key.split('_to_')
                prev_year, current_year = years[0], years[1]

                result += f"**{prev_year} → {current_year}:**\n"

                # Revenue
                rev_growth = data['revenue_growth']
                trend_emoji = "📈" if rev_growth > 0 else "📉" if rev_growth < 0 else "➡️"
                result += f"   {trend_emoji} Revenue: {rev_growth:+.1f}%\n"

                # Margin
                margin_growth = data['margin_growth']
                trend_emoji = "📈" if margin_growth > 0 else "📉" if margin_growth < 0 else "➡️"
                result += f"   {trend_emoji} Gross Margin: {margin_growth:+.1f}%\n"

                # Transactions
                trans_growth = data['transaction_growth']
                trend_emoji = "📈" if trans_growth > 0 else "📉" if trans_growth < 0 else "➡️"
                result += f"   {trend_emoji} Transactions: {trans_growth:+.1f}%\n\n"

            return result

        except Exception as e:
            return f"❌ Error in general comparison: {e}"


    def handle_channel_query(self, query):
        """Handle channel specific queries with comprehensive multi-year and regional analysis using interactive HTML tables"""
        import re
        import pandas as pd
        
        try:
            print(f"DEBUG: Channel handler called with: {query}")
            
            # Check if Channel column exists
            channel_column = 'Channel'
            if channel_column not in self.df.columns:
                print("DEBUG: No Channel column found")
                return "❌ Channel data not available in this dataset"
            
            print(f"DEBUG: Available columns: {list(self.df.columns)}")
            
            # Extract channel name with improved matching strategy
            channel_name = None
            query_lower = query.lower()
            
            # Get all available channels
            available_channels = [str(c) for c in self.df['Channel'].dropna().unique()]
            
            # CRITICAL FIX: Filter out problematic single character channels like "-" during matching
            # but keep them for the final error message
            matching_channels = [c for c in available_channels if len(c) > 1 or c.isalnum()]
            problem_channels = [c for c in available_channels if c not in matching_channels]
            
            # Sort channels by length (longest first) to avoid partial matches
            matching_channels_sorted = sorted(matching_channels, key=len, reverse=True)
            
            print(f"DEBUG: Available channels: {available_channels}")
            print(f"DEBUG: Matching channels: {matching_channels_sorted}")
            print(f"DEBUG: Problem channels: {problem_channels}")
            
            # Try multiple regex patterns for channel extraction
            patterns = [
                r'channel\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'channel\s+(.+?)(?:\s+in\s+year|\s+for\s+year|\s+during|\s+\d{4}|$)',
                r'of\s+channel\s+([^,\n]+?)(?:\s+(?:in|for|during|year|\d{4})|$)',
                r'(?:show|performance).*?(?:for|of)\s+([^,\n]+?)(?:\s+channel|$)'
            ]
            
            channel_match = None
            for pattern in patterns:
                channel_match = re.search(pattern, query_lower)
                if channel_match:
                    print(f"DEBUG: Channel extracted with pattern: {pattern}")
                    break
            
            # If no regex match, try direct matching with available channels
            if not channel_match:
                print("DEBUG: No regex match, trying direct channel matching")
                matched_directly = None
                for channel in available_channels:
                    if channel.lower() in query_lower:
                        matched_directly = channel
                        print(f"DEBUG: Direct match found: {channel}")
                        break
                
                # Create a simple object with group method if we found a direct match
                if matched_directly:
                    class DirectMatch:
                        def __init__(self, value):
                            self.value = value
                        def group(self, index):
                            return self.value
                    channel_match = DirectMatch(matched_directly)
            
            if not channel_match:
                print("DEBUG: No channel match found")
                valid_channels = [c for c in available_channels if c != "-" or len(available_channels) == 1]
                return f"❌ Please specify a valid channel name. Available channels: {', '.join(valid_channels[:5])}"
            
            requested_channel = channel_match.group(1).strip()
            print(f"DEBUG: Extracted channel: '{requested_channel}'")
            
            # Find exact match (case insensitive) - improved matching
            matched_channel = None
            
            print(f"DEBUG: Available Channels: {list(available_channels)}")
            
            # Try exact match first
            for channel in available_channels:
                if str(channel).lower().strip() == requested_channel.lower().strip():
                    matched_channel = channel
                    print(f"DEBUG: Exact match found: {matched_channel}")
                    break
            
            # Try partial match if exact fails
            if not matched_channel:
                for channel in available_channels:
                    if requested_channel.lower().strip() in str(channel).lower().strip():
                        matched_channel = channel
                        print(f"DEBUG: Partial match found: {matched_channel}")
                        break
            
            if not matched_channel:
                print(f"DEBUG: No match found for '{requested_channel}'")
                valid_channels = [c for c in available_channels if c != "-" or len(available_channels) == 1]
                return f"❌ Channel '{requested_channel}' not found. Available: {', '.join(valid_channels[:5])}"
            
            print(f"DEBUG: Final matched channel: '{matched_channel}'")
            
            # Get all data for this channel
            channel_data = self.df[self.df[channel_column].str.lower() == matched_channel.lower()]
            available_years = sorted(channel_data['Year_Start'].unique())
            
            if len(available_years) == 0:
                return f"ℹ️ No data found for channel {matched_channel}"
            
            print(f"DEBUG: Available years for {matched_channel}: {available_years}")
            
            # Handle simple growth/transaction queries (maintain backward compatibility)
            if ('growth' in query_lower or 'transaction count' in query_lower) and 'performance' not in query_lower:
                year = None
                year_match = re.search(r'(?:fy)?(20)?(\d{2})', query_lower)
                if year_match:
                    year = 2000 + int(year_match.group(2))
                
                if 'growth' in query_lower and year:
                    # Handle growth queries
                    current_data = channel_data[channel_data['Year_Start'] == year]
                    prev_year = year - 1
                    prev_data = channel_data[channel_data['Year_Start'] == prev_year]
                    
                    if len(prev_data) == 0 or len(current_data) == 0:
                        return f"❌ Cannot calculate growth - missing data for {prev_year} or {year}"
                    
                    # Calculate metrics
                    current_revenue = current_data['TL Base Value'].sum()
                    prev_revenue = prev_data['TL Base Value'].sum()
                    revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                    
                    current_margin = current_data['Gross Margin Value'].sum()
                    prev_margin = prev_data['Gross Margin Value'].sum()
                    margin_growth = ((current_margin - prev_margin) / prev_margin * 100) if prev_margin > 0 else 0
                    
                    current_count = len(current_data)
                    prev_count = len(prev_data)
                    count_growth = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                    
                    return (f"📈 Channel {matched_channel} Growth (FY{prev_year}→FY{year}):\n"
                        f"   • Revenue Growth: {revenue_growth:+.1f}%\n"
                        f"   • Gross Margin Growth: {margin_growth:+.1f}%\n"
                        f"   • Transaction Growth: {count_growth:+.1f}%")
                
                elif 'transaction count' in query_lower:
                    if year:
                        year_data = channel_data[channel_data['Year_Start'] == year]
                        transaction_count = len(year_data)
                        return f"📊 Channel {matched_channel} Transactions in {year}: {transaction_count:,}"
                    else:
                        transaction_count = len(channel_data)
                        return f"📊 Channel {matched_channel} Total Transactions: {transaction_count:,}"
            
            # Check if partner data is available
            partner_column = None
            possible_partner_columns = ['Partner Name', 'Partner', 'Channel Partner', 'Reseller', 'Distributor']
            for col in possible_partner_columns:
                if col in self.df.columns:
                    partner_column = col
                    break
            
            # Build comprehensive output with interactive HTML tables
            output_text = f"## PERFORMANCE FOR {matched_channel.upper()} CHANNEL\n\n"
            
            # Year-wise performance summary table
            yearly_summary_data = []
            yearly_partner_data = {}  # Store partner data for each year
            
            for year in available_years:
                year_data = channel_data[channel_data['Year_Start'] == year]
                prev_year = year - 1
                prev_year_data = channel_data[channel_data['Year_Start'] == prev_year]
                
                # Calculate current year metrics
                total_revenue = year_data['TL Base Value'].sum()
                total_margin = year_data['Gross Margin Value'].sum()
                gm_percent = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                transaction_count = len(year_data)
                
                # Get top 5 partners for this year
                year_partners = []
                if partner_column and partner_column in year_data.columns:
                    partner_stats = year_data[year_data[partner_column].notna()].groupby(partner_column).agg(
                        Revenue=('TL Base Value', 'sum'),
                        Margin=('Gross Margin Value', 'sum'),
                        Transactions=('TL Base Value', 'count')
                    ).reset_index().sort_values('Revenue', ascending=False).head(5)
                    
                    for _, partner_row in partner_stats.iterrows():
                        partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                        year_partners.append({
                            'name': str(partner_row[partner_column])[:25],  # Truncate long names
                            'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                            'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                            'gm_percent': f"{partner_gm_percent:.1f}%",
                            'transactions': f"{int(partner_row['Transactions']):,}"
                        })
                
                yearly_partner_data[year] = year_partners
                
                # Calculate growth
                tl_growth_str = "N/A"
                gm_growth_str = "N/A"
                txn_growth_str = "N/A"
                
                if len(prev_year_data) > 0:
                    prev_revenue = prev_year_data['TL Base Value'].sum()
                    prev_margin = prev_year_data['Gross Margin Value'].sum()
                    prev_count = len(prev_year_data)
                    
                    if prev_revenue > 0:
                        tl_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
                        tl_growth_str = f"{tl_growth:+.1f}%"
                    
                    if prev_margin > 0:
                        gm_growth = ((total_margin - prev_margin) / prev_margin * 100)
                        gm_growth_str = f"{gm_growth:+.1f}%"
                    
                    if prev_count > 0:
                        txn_growth = ((transaction_count - prev_count) / prev_count * 100)
                        txn_growth_str = f"{txn_growth:+.1f}%"
                
                # Format year string
                year_str = f"{year}-{str(year+1)[2:]}"
                
                yearly_summary_data.append({
                    'Year': year_str,
                    'TL (₹Cr)': f"₹{total_revenue/10000000:.2f}",
                    'GM (₹Cr)': f"₹{total_margin/10000000:.2f}",
                    'GM%': f"{gm_percent:.1f}%",
                    'Transactions': f"{transaction_count:,}",
                    'TL Growth': tl_growth_str,
                    'GM Growth': gm_growth_str,
                    'Txn Growth': txn_growth_str,
                    'year_key': year  # For linking with partner data
                })
            
            # Create interactive yearly summary table
            if yearly_summary_data:
                yearly_df = pd.DataFrame(yearly_summary_data)
                yearly_table_html = self._generate_interactive_html_table(
                    yearly_df,
                    yearly_partner_data,
                    table_id=f"{matched_channel.lower().replace(' ', '_').replace('-', '_')}_yearly_summary",
                    title=f"{matched_channel} Channel - Yearly Performance",
                    table_type="yearly"
                )
                output_text += yearly_table_html + "\n\n"
            
            # Regional Analysis Section
            region_column = 'Region'
            if region_column in channel_data.columns:
                output_text += "### REGIONAL PERFORMANCE\n\n"
                
                # Regional summary for each year
                for year in available_years:
                    year_data = channel_data[channel_data['Year_Start'] == year]
                    prev_year_data = channel_data[channel_data['Year_Start'] == year - 1]
                    
                    # Filter out null/empty regions
                    year_filtered = year_data[year_data[region_column].notna() & (year_data[region_column] != '')]
                    
                    if year_filtered.empty:
                        continue
                    
                    # Current year stats by region
                    current_stats = year_filtered.groupby(region_column).agg(
                        TL_Current=('TL Base Value', 'sum'),
                        GM_Current=('Gross Margin Value', 'sum'),
                        Txn_Current=('TL Base Value', 'count')
                    ).reset_index().sort_values('TL_Current', ascending=False)
                    
                    # Get partner data for each region
                    regional_partner_data = {}
                    for _, region_row in current_stats.iterrows():
                        region_name = region_row[region_column]
                        region_data = year_filtered[year_filtered[region_column] == region_name]
                        
                        region_partners = []
                        if partner_column and partner_column in region_data.columns:
                            partner_stats = region_data[region_data[partner_column].notna()].groupby(partner_column).agg(
                                Revenue=('TL Base Value', 'sum'),
                                Margin=('Gross Margin Value', 'sum'),
                                Transactions=('TL Base Value', 'count')
                            ).reset_index().sort_values('Revenue', ascending=False).head(5)
                            
                            for _, partner_row in partner_stats.iterrows():
                                partner_gm_percent = (partner_row['Margin'] / partner_row['Revenue'] * 100) if partner_row['Revenue'] > 0 else 0
                                region_partners.append({
                                    'name': str(partner_row[partner_column])[:25],
                                    'revenue': f"₹{partner_row['Revenue']/10000000:.2f}Cr",
                                    'margin': f"₹{partner_row['Margin']/10000000:.2f}Cr",
                                    'gm_percent': f"{partner_gm_percent:.1f}%",
                                    'transactions': f"{int(partner_row['Transactions']):,}"
                                })
                        
                        regional_partner_data[region_name] = region_partners
                    
                    # Previous year stats for growth calculation
                    prev_stats = pd.DataFrame()
                    if not prev_year_data.empty and region_column in prev_year_data.columns:
                        prev_filtered = prev_year_data[prev_year_data[region_column].notna() & (prev_year_data[region_column] != '')]
                        if not prev_filtered.empty:
                            prev_stats = prev_filtered.groupby(region_column).agg(
                                TL_Prev=('TL Base Value', 'sum'),
                                GM_Prev=('Gross Margin Value', 'sum'),
                                Txn_Prev=('TL Base Value', 'count')
                            ).reset_index()
                    
                    # Merge with previous year data
                    if not prev_stats.empty:
                        merged_stats = pd.merge(current_stats, prev_stats, on=region_column, how='left')
                    else:
                        merged_stats = current_stats
                        merged_stats['TL_Prev'] = 0
                        merged_stats['GM_Prev'] = 0
                        merged_stats['Txn_Prev'] = 0
                    
                    merged_stats = merged_stats.fillna(0)
                    
                    if merged_stats.empty:
                        continue
                    
                    # Calculate metrics for display
                    table_data = []
                    for idx, row in merged_stats.iterrows():
                        region_name = str(row[region_column])[:30]  # Truncate long names
                        
                        # Current year calculations
                        gm_percent = (row['GM_Current'] / row['TL_Current'] * 100) if row['TL_Current'] > 0 else 0
                        
                        # Growth calculations
                        tl_prev_val = float(row['TL_Prev'])
                        gm_prev_val = float(row['GM_Prev'])
                        txn_prev_val = float(row['Txn_Prev'])
                        
                        tl_growth_str = "N/A"
                        gm_growth_str = "N/A"
                        txn_growth_str = "N/A"
                        
                        if tl_prev_val > 0:
                            tl_growth = (row['TL_Current'] - tl_prev_val) / tl_prev_val * 100
                            tl_growth_str = f"{tl_growth:+.1f}%"
                        elif row['TL_Current'] > 0:
                            tl_growth_str = "New"
                        
                        if gm_prev_val > 0:
                            gm_growth = (row['GM_Current'] - gm_prev_val) / gm_prev_val * 100
                            gm_growth_str = f"{gm_growth:+.1f}%"
                        elif row['GM_Current'] > 0:
                            gm_growth_str = "New"
                        
                        if txn_prev_val > 0:
                            txn_growth = (row['Txn_Current'] - txn_prev_val) / txn_prev_val * 100
                            txn_growth_str = f"{txn_growth:+.1f}%"
                        elif row['Txn_Current'] > 0:
                            txn_growth_str = "New"
                        
                        table_data.append({
                            'Region': region_name,
                            'TL (₹Cr)': f"₹{row['TL_Current']/10000000:.2f}",
                            'GM (₹Cr)': f"₹{row['GM_Current']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Transactions': f"{int(row['Txn_Current']):,}",
                            'TL Growth': tl_growth_str,
                            'GM Growth': gm_growth_str,
                            'Txn Growth': txn_growth_str,
                            'region_key': str(row[region_column])  # For linking with partner data
                        })
                    
                    if table_data:
                        year_str = f"{year}-{str(year+1)[2:]}"
                        output_text += f"**{year_str}:**\n\n"
                        
                        # Create DataFrame and generate interactive HTML table
                        region_df = pd.DataFrame(table_data)
                        table_html = self._generate_interactive_html_table(
                            region_df,
                            regional_partner_data,
                            table_id=f"{matched_channel.lower().replace(' ', '_').replace('-', '_')}_regional_{year}",
                            title=f"Regional Performance - {year_str}",
                            table_type="regional"
                        )
                        output_text += table_html + "\n\n"
            else:
                output_text += "### REGIONAL PERFORMANCE\n❌ Region column not found in data\n\n"
            
            # Customer Analysis Section (if available)
            customer_column = 'Customer'
            if customer_column in channel_data.columns:
                output_text += "### TOP CUSTOMERS ANALYSIS\n\n"
                
                # Get top customers by total revenue across all years
                customer_stats = channel_data.groupby(customer_column).agg(
                    Total_TL=('TL Base Value', 'sum'),
                    Total_GM=('Gross Margin Value', 'sum'),
                    Total_Txn=('TL Base Value', 'count')
                ).reset_index().sort_values('Total_TL', ascending=False).head(10)
                
                if not customer_stats.empty:
                    customer_table_data = []
                    for idx, row in customer_stats.iterrows():
                        customer_name = str(row[customer_column])[:40]  # Truncate long names
                        gm_percent = (row['Total_GM'] / row['Total_TL'] * 100) if row['Total_TL'] > 0 else 0
                        
                        customer_table_data.append({
                            'Customer': customer_name,
                            'Total TL (₹Cr)': f"₹{row['Total_TL']/10000000:.2f}",
                            'Total GM (₹Cr)': f"₹{row['Total_GM']/10000000:.2f}",
                            'GM%': f"{gm_percent:.1f}%",
                            'Total Transactions': f"{int(row['Total_Txn']):,}"
                        })
                    
                    if customer_table_data:
                        customer_df = pd.DataFrame(customer_table_data)
                        customer_table_html = self._generate_html_table(
                            customer_df,
                            table_id=f"{matched_channel.lower().replace(' ', '_').replace('-', '_')}_top_customers",
                            title=f"Top Customers - All Years Combined",
                            highlight_total=False
                        )
                        output_text += customer_table_html + "\n\n"
            
            print(f"DEBUG: Generated comprehensive interactive HTML table report for {matched_channel}")
            return output_text
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return f"❌ Error processing channel query: {str(e)}"
    
    def handle_multidimensional_query(self, user_query):
        """Handle queries with multiple dimensions (Year, Channel, Region, Vertical, Partner, OEM, End Customer)"""
        try:
            # Map query terms to column names
            dimension_map = {
                'year': 'Year_Start',
                'channel': 'Channel',
                'region': 'Region',
                'vertical': 'Vertical',
                'account': 'Vertical',  # Alias for vertical
                'partner': 'Partner',
                'oem': 'OEM',
                'customer': 'End Customer',
                'end customer': 'End Customer'
            }

            # Extract requested dimensions from query
            requested_dims = []
            for term, col in dimension_map.items():
                if term in user_query.lower() and col in self.df.columns:
                    requested_dims.append(col)

            if not requested_dims:
                return None

            # Check if we have a pre-computed combination
            dim_key = "_".join(sorted(requested_dims))
            if dim_key in self.dimension_combinations:
                grouped = self.dimension_combinations[dim_key]
            else:
                # Extract filter values
                filters = {}
                for dim in requested_dims:
                    dim_values = []
                    # Check for specific values mentioned
                    unique_vals = self.processor.get_unique_values(dim)
                    for val in unique_vals:
                        # Handle numeric values (like years)
                        str_val = str(val)
                        if str_val.lower() in user_query.lower():
                            dim_values.append(val)
                    if dim_values:
                        filters[dim] = dim_values

                # Apply filters
                filtered_df = self.processor.filter_data(filters) if filters else self.df

                # Group by requested dimensions
                if filtered_df.empty:
                    return "❌ No data matches your filters"

                grouped = filtered_df.groupby(requested_dims).agg({
                    'TL Base Value': 'sum',
                    'Gross Margin Value': 'sum'
                }).reset_index()

            # Determine metric
            if 'margin' in user_query or 'gm' in user_query:
                metric_col = 'Gross Margin Value'
                metric_name = 'Gross Margin'
            else:  # Default to revenue
                metric_col = 'TL Base Value'
                metric_name = 'Revenue'

            # Sort by the metric
            grouped = grouped.sort_values(metric_col, ascending=False)

            # Format results
            result = f"📊 {metric_name} Breakdown"
            if 'filter' in user_query or 'where' in user_query:
                filter_desc = []
                for dim in requested_dims:
                    unique_vals = grouped[dim].unique()
                    if len(unique_vals) < 5:  # Only show filter if limited values
                        filter_desc.append(f"{dim.replace('_', ' ')}: {', '.join(map(str, unique_vals))}")
                if filter_desc:
                    result += f" (Filtered by: {', '.join(filter_desc)})"
            result += ":\n\n"

            # Format dimension headers
            dim_headers = " | ".join([d.replace('_', ' ') for d in requested_dims])
            result += f"**{dim_headers}**\n"

            for _, row in grouped.head(10).iterrows():
                dim_values = " | ".join([str(row[dim]) for dim in requested_dims])
                result += f"• {dim_values}: {format_in_crores(row[metric_col])}\n"

            # Add total row count if filtered
            if len(grouped) < len(self.df):
                result += f"\nTotal Records: {len(grouped):,}"
            return result

        except Exception as e:
            print(f"Multi-dim query error: {e}")
            return f"❌ Error processing multi-dimensional query: {e}"

    def handle_ai_query(self, user_query):
        """Use AI for complex queries"""
        try:
            # Create context about the data
            context = self.create_data_context()

            # Create the prompt
            prompt = f"""
            You are a sales data analyst. Here's information about the dataset:

            {context}

            User question: {user_query}

            Please provide a helpful response based on the data context. If you need specific calculations, suggest what analysis would be useful.
            Keep your response concise and business-focused.
            """

            response = model.generate_content(prompt)
            return f"🤖 AI Analysis:\n{response.text}"

        except Exception as e:
            return f"❌ Error processing query: {e}"

    def create_data_context(self):
        """Create context about the dataset for AI"""
        context = f"""
        Dataset Overview:
        - Total Records: {len(self.df):,}
        - Total Columns: {len(self.df.columns)}
        - Key Metrics Available: {', '.join(self.df.select_dtypes(include=['number']).columns.tolist())}

        Summary Statistics:
        """

        # Add key statistics
        for key, value in self.stats.items():
            if isinstance(value, (int, float)):
                context += f"- {key.replace('_', ' ').title()}: {format_in_crores(value)}\n"
            elif isinstance(value, list):
                context += f"- {key.replace('_', ' ').title()}: {len(value)} unique values\n"

        # Add yearly overview
        years = [y for y in self.yearly_stats.keys() if y != 'comparisons']
        if years:
            context += f"\nYearly Data Available: {sorted(years)}\n"

        # Add partner/OEM information
        if self.partner_stats:
            context += f"\nPartner Statistics Available for {len(self.partner_stats)} partners\n"
        if self.oem_stats:
            context += f"\nOEM Statistics Available for {len(self.oem_stats)} OEMs\n"
        if self.partner_customer_stats:
            context += f"\nPartner-Customer Relationship Data Available for {len(self.partner_customer_stats)} partners\n"
        if self.vertical_stats:
            context += f"\nVertical Statistics Available for {len(self.vertical_stats)} verticals\n"
        if self.customer_stats:
            context += f"\nEnd Customer Statistics Available for {len(self.customer_stats)} customers\n"

        # Add dimension information
        context += f"\nAvailable Dimensions:\n"
        dimensions = ['Year_Start', 'Year_End', 'Channel', 'Region', 'Vertical', 'Partner', 'OEM', 'End Customer']
        for dim in dimensions:
            if dim in self.df.columns:
                unique_count = len(self.df[dim].unique())
                context += f"- {dim.replace('_', ' ')}: {unique_count} unique values\n"

        # Add pre-computed combinations
        if self.dimension_combinations:
            context += f"\nPre-computed Dimension Combinations:\n"
            for combo in sorted(self.dimension_combinations.keys()):
                context += f"- {combo.replace('_', ' x ')}\n"

        return context

    def create_visualization(self, query_type, data=None):
        """Create visualizations for queries"""
        try:
            from plotly.subplots import make_subplots
            
            if query_type == 'regional_sales' and 'Region' in self.df.columns:
                regional_data = self.df.groupby('Region')['TL Base Value'].sum().reset_index()
                fig = px.bar(regional_data, x='Region', y='TL Base Value',
                        title='Sales by Region (in Crores)',
                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                fig.show(renderer="browser")

            elif query_type == 'yearly_trend' and 'Year_Start' in self.df.columns:
                yearly_data = self.df.groupby('Year_Start')['TL Base Value'].sum().reset_index()
                fig = px.line(yearly_data, x='Year_Start', y='TL Base Value',
                            title='Sales Trend by Year (in Crores)',
                            labels={'TL Base Value': 'Revenue (₹ Cr)'})
                fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                fig.show(renderer="browser")

            elif query_type == 'yearly_comparison':
                if hasattr(self, 'yearly_stats') and self.yearly_stats:
                    years = [y for y in self.yearly_stats.keys() if y != 'comparisons']
                    if len(years) >= 2:
                        revenue_data = []
                        margin_data = []
                        for year in sorted(years):
                            year_data = self.yearly_stats.get(year, {})
                            revenue_data.append(year_data.get('total_revenue', 0) / 10000000)
                            margin_data.append(year_data.get('total_gross_margin', 0) / 10000000)

                        fig = go.Figure()
                        fig.add_trace(go.Bar(name='Revenue', x=years, y=revenue_data))
                        fig.add_trace(go.Bar(name='Gross Margin', x=years, y=margin_data))
                        fig.update_layout(
                            title='Year-over-Year Revenue and Gross Margin Comparison (in Crores)',
                            yaxis_title='Amount (₹ Cr)',
                            yaxis_tickprefix='₹',
                            yaxis_tickformat=',.2f'
                        )
                        fig.show(renderer="browser")
                else:
                    print("No yearly statistics data available")

            elif query_type == 'channel_performance':
                if 'Channel' in self.df.columns:
                    channel_data = self.df.groupby('Channel')['TL Base Value'].sum().reset_index()
                    channel_data['TL Base Value'] = channel_data['TL Base Value'] / 10000000
                    fig = px.pie(channel_data, values='TL Base Value', names='Channel',
                            title='Revenue Distribution by Channel (in Crores)')
                    fig.show(renderer="browser")

            elif query_type == 'partner_regional':
                if data and hasattr(self, 'partner_stats') and self.partner_stats:
                    partner_name = data.get('partner_name')
                    partner_data = self.partner_stats.get(partner_name)
                    if partner_name and partner_data:
                        regional_revenue = partner_data.get('regional_revenue', {})
                        if regional_revenue:
                            regional_data = pd.DataFrame.from_dict(
                                regional_revenue,
                                orient='index',
                                columns=['Revenue']
                            ).reset_index()
                            regional_data.columns = ['Region', 'Revenue']
                            regional_data['Revenue'] = regional_data['Revenue'] / 10000000

                            fig = px.bar(regional_data, x='Region', y='Revenue',
                                        title=f'Regional Revenue for {partner_name} (in Crores)',
                                        labels={'Revenue': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                        else:
                            print(f"No regional revenue data available for partner: {partner_name}")
                    else:
                        print(f"Partner '{partner_name}' not found or has no data")
                else:
                    print("No partner statistics data available or partner name not provided")

            elif query_type == 'partner_yearly':
                if data and hasattr(self, 'partner_stats') and self.partner_stats:
                    partner_name = data.get('partner_name')
                    partner_data = self.partner_stats.get(partner_name)
                    if partner_name and partner_data:
                        yearly_revenue = partner_data.get('yearly_revenue', {})
                        if yearly_revenue:
                            yearly_data = pd.DataFrame.from_dict(
                                yearly_revenue,
                                orient='index',
                                columns=['Revenue']
                            ).reset_index()
                            yearly_data.columns = ['Year', 'Revenue']
                            yearly_data['Revenue'] = yearly_data['Revenue'] / 10000000

                            fig = px.line(yearly_data, x='Year', y='Revenue',
                                        title=f'Yearly Revenue Trend for {partner_name} (in Crores)',
                                        labels={'Revenue': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                        else:
                            print(f"No yearly revenue data available for partner: {partner_name}")
                    else:
                        print(f"Partner '{partner_name}' not found or has no data")
                else:
                    print("No partner statistics data available or partner name not provided")

            elif query_type == 'partner_vertical':
                if data and hasattr(self, 'partner_stats') and self.partner_stats:
                    partner_name = data.get('partner_name')
                    partner_data = self.partner_stats.get(partner_name)
                    if partner_name and partner_data and 'vertical_revenue' in partner_data:
                        vertical_data = pd.DataFrame.from_dict(
                            partner_data['vertical_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        vertical_data.columns = ['Vertical', 'Revenue']
                        vertical_data['Revenue'] = vertical_data['Revenue'] / 10000000

                        fig = px.bar(vertical_data, x='Vertical', y='Revenue',
                                    title=f'Vertical Revenue for {partner_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No vertical revenue data available for partner: {partner_name}")
                else:
                    print("No partner statistics data available or partner name not provided")

            elif query_type == 'oem_regional':
                if data and hasattr(self, 'oem_stats') and self.oem_stats:
                    oem_name = data.get('oem_name')
                    oem_data = self.oem_stats.get(oem_name)
                    if oem_name and oem_data:
                        regional_revenue = oem_data.get('regional_revenue', {})
                        if regional_revenue:
                            regional_data = pd.DataFrame.from_dict(
                                regional_revenue,
                                orient='index',
                                columns=['Revenue']
                            ).reset_index()
                            regional_data.columns = ['Region', 'Revenue']
                            regional_data['Revenue'] = regional_data['Revenue'] / 10000000

                            fig = px.bar(regional_data, x='Region', y='Revenue',
                                        title=f'Regional Revenue for {oem_name} (in Crores)',
                                        labels={'Revenue': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                        else:
                            print(f"No regional revenue data available for OEM: {oem_name}")
                    else:
                        print(f"OEM '{oem_name}' not found or has no data")
                else:
                    print("No OEM statistics data available or OEM name not provided")

            elif query_type == 'oem_yearly':
                if data and hasattr(self, 'oem_stats') and self.oem_stats:
                    oem_name = data.get('oem_name')
                    oem_data = self.oem_stats.get(oem_name)
                    if oem_name and oem_data:
                        yearly_revenue = oem_data.get('yearly_revenue', {})
                        if yearly_revenue:
                            yearly_data = pd.DataFrame.from_dict(
                                yearly_revenue,
                                orient='index',
                                columns=['Revenue']
                            ).reset_index()
                            yearly_data.columns = ['Year', 'Revenue']
                            yearly_data['Revenue'] = yearly_data['Revenue'] / 10000000

                            fig = px.line(yearly_data, x='Year', y='Revenue',
                                        title=f'Yearly Revenue Trend for {oem_name} (in Crores)',
                                        labels={'Revenue': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                        else:
                            print(f"No yearly revenue data available for OEM: {oem_name}")
                    else:
                        print(f"OEM '{oem_name}' not found or has no data")
                else:
                    print("No OEM statistics data available or OEM name not provided")

            elif query_type == 'oem_vertical':
                if data and hasattr(self, 'oem_stats') and self.oem_stats:
                    oem_name = data.get('oem_name')
                    oem_data = self.oem_stats.get(oem_name)
                    if oem_name and oem_data and 'vertical_revenue' in oem_data:
                        vertical_data = pd.DataFrame.from_dict(
                            oem_data['vertical_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        vertical_data.columns = ['Vertical', 'Revenue']
                        vertical_data['Revenue'] = vertical_data['Revenue'] / 10000000

                        fig = px.bar(vertical_data, x='Vertical', y='Revenue',
                                    title=f'Vertical Revenue for {oem_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No vertical revenue data available for OEM: {oem_name}")
                else:
                    print("No OEM statistics data available or OEM name not provided")

            elif query_type == 'partner_customers':
                if data and hasattr(self, 'partner_customer_stats') and self.partner_customer_stats:
                    partner_name = data.get('partner_name')
                    partner_customer_data = self.partner_customer_stats.get(partner_name)
                    if partner_name and partner_customer_data:
                        customer_data = pd.DataFrame(partner_customer_data['customer_details'])
                        customer_data['Total Revenue'] = customer_data['Total Revenue'] / 10000000

                        fig = px.bar(customer_data, x='End Customer', y='Total Revenue',
                                    title=f'Top Customers for {partner_name} (in Crores)',
                                    labels={'Total Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No customer data available for partner: {partner_name}")
                else:
                    print("No partner customer statistics data available or partner name not provided")

            elif query_type == 'vertical_regional':
                if data and hasattr(self, 'vertical_stats') and self.vertical_stats:
                    vertical_name = data.get('vertical_name')
                    vertical_data = self.vertical_stats.get(vertical_name)
                    if vertical_name and vertical_data and 'regional_revenue' in vertical_data:
                        regional_data = pd.DataFrame.from_dict(
                            vertical_data['regional_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        regional_data.columns = ['Region', 'Revenue']
                        regional_data['Revenue'] = regional_data['Revenue'] / 10000000

                        fig = px.bar(regional_data, x='Region', y='Revenue',
                                    title=f'Regional Revenue for {vertical_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No regional revenue data available for vertical: {vertical_name}")
                else:
                    print("No vertical statistics data available or vertical name not provided")

            elif query_type == 'vertical_yearly':
                if data and hasattr(self, 'vertical_stats') and self.vertical_stats:
                    vertical_name = data.get('vertical_name')
                    vertical_data = self.vertical_stats.get(vertical_name)
                    if vertical_name and vertical_data and 'yearly_revenue' in vertical_data:
                        yearly_data = pd.DataFrame.from_dict(
                            vertical_data['yearly_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        yearly_data.columns = ['Year', 'Revenue']
                        yearly_data['Revenue'] = yearly_data['Revenue'] / 10000000

                        fig = px.line(yearly_data, x='Year', y='Revenue',
                                    title=f'Yearly Revenue Trend for {vertical_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No yearly revenue data available for vertical: {vertical_name}")
                else:
                    print("No vertical statistics data available or vertical name not provided")

            elif query_type == 'customer_regional':
                if data and hasattr(self, 'customer_stats') and self.customer_stats:
                    customer_name = data.get('customer_name')
                    customer_data = self.customer_stats.get(customer_name)
                    if customer_name and customer_data and 'regional_revenue' in customer_data:
                        regional_data = pd.DataFrame.from_dict(
                            customer_data['regional_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        regional_data.columns = ['Region', 'Revenue']
                        regional_data['Revenue'] = regional_data['Revenue'] / 10000000

                        fig = px.bar(regional_data, x='Region', y='Revenue',
                                    title=f'Regional Revenue for {customer_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No regional revenue data available for customer: {customer_name}")
                else:
                    print("No customer statistics data available or customer name not provided")

            elif query_type == 'customer_yearly':
                if data and hasattr(self, 'customer_stats') and self.customer_stats:
                    customer_name = data.get('customer_name')
                    customer_data = self.customer_stats.get(customer_name)
                    if customer_name and customer_data and 'yearly_revenue' in customer_data:
                        yearly_data = pd.DataFrame.from_dict(
                            customer_data['yearly_revenue'],
                            orient='index',
                            columns=['Revenue']
                        ).reset_index()
                        yearly_data.columns = ['Year', 'Revenue']
                        yearly_data['Revenue'] = yearly_data['Revenue'] / 10000000

                        fig = px.line(yearly_data, x='Year', y='Revenue',
                                    title=f'Yearly Revenue Trend for {customer_name} (in Crores)',
                                    labels={'Revenue': 'Revenue (₹ Cr)'})
                        fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                        fig.show(renderer="browser")
                    else:
                        print(f"No yearly revenue data available for customer: {customer_name}")
                else:
                    print("No customer statistics data available or customer name not provided")

            elif query_type == 'oem_partner_customer':
                if data and all(k in data for k in ['oem_name', 'partner_name', 'customer_name']):
                    dim_key = "OEM_Partner_EndCustomer_Year_Start"
                    if dim_key in self.dimension_combinations:
                        filtered = self.dimension_combinations[dim_key]
                        filtered = filtered[
                            (filtered['OEM'] == data['oem_name']) & 
                            (filtered['Partner'] == data['partner_name']) &
                            (filtered['End Customer'] == data['customer_name'])
                        ]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.bar(filtered, 
                                        x='Year_Start', 
                                        y='TL Base Value',
                                        title=f"Revenue for {data['oem_name']} + {data['partner_name']} + {data['customer_name']}",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)', 'Year_Start': 'Year'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying OEM-Partner-Customer relationship"
                    return "❌ No relationship data available"

            elif query_type == 'personnel_performance_trend':
                if data and 'person_name' in data and 'role' in data:
                    role_column = data['role'].replace('_', ' ')
                    
                    # Yearly trend
                    yearly_dim_key = f"{data['role']}_Year_Start"
                    yearly_data = self.dimension_combinations.get(yearly_dim_key, pd.DataFrame())
                    if not yearly_data.empty:
                        yearly_data = yearly_data[yearly_data[role_column] == data['person_name']]
                        yearly_data = yearly_data.groupby('Year_Start')['TL Base Value'].sum().reset_index()
                        yearly_data['TL Base Value'] = yearly_data['TL Base Value'] / 10000000
                    
                    # OEM performance
                    oem_dim_key = f"{data['role']}_OEM"
                    oem_data = self.dimension_combinations.get(oem_dim_key, pd.DataFrame())
                    if not oem_data.empty:
                        oem_data = oem_data[oem_data[role_column] == data['person_name']]
                        oem_data = oem_data.groupby('OEM')['TL Base Value'].sum().reset_index()
                        oem_data['TL Base Value'] = oem_data['TL Base Value'] / 10000000
                        oem_data = oem_data.sort_values('TL Base Value', ascending=False).head(5)
                    
                    # Partner performance
                    partner_dim_key = f"{data['role']}_Partner"
                    partner_data = self.dimension_combinations.get(partner_dim_key, pd.DataFrame())
                    if not partner_data.empty:
                        partner_data = partner_data[partner_data[role_column] == data['person_name']]
                        partner_data = partner_data.groupby('Partner')['TL Base Value'].sum().reset_index()
                        partner_data['TL Base Value'] = partner_data['TL Base Value'] / 10000000
                        partner_data = partner_data.sort_values('TL Base Value', ascending=False).head(5)
                    
                    # Vertical performance
                    vertical_dim_key = f"{data['role']}_Vertical"
                    vertical_data = self.dimension_combinations.get(vertical_dim_key, pd.DataFrame())
                    if not vertical_data.empty:
                        vertical_data = vertical_data[vertical_data[role_column] == data['person_name']]
                        vertical_data = vertical_data.groupby('Vertical')['TL Base Value'].sum().reset_index()
                        vertical_data['TL Base Value'] = vertical_data['TL Base Value'] / 10000000
                        vertical_data = vertical_data.sort_values('TL Base Value', ascending=False).head(5)
                    
                    # Create figure if we have data
                    if not yearly_data.empty:
                        fig = make_subplots(
                            rows=2, cols=2,
                            subplot_titles=(
                                'Yearly Revenue Trend',
                                'Top OEMs by Revenue',
                                'Top Partners by Revenue',
                                'Top Verticals by Revenue'
                            )
                        )
                        
                        # Yearly trend
                        fig.add_trace(
                            go.Scatter(
                                x=yearly_data['Year_Start'],
                                y=yearly_data['TL Base Value'],
                                mode='lines+markers',
                                name='Revenue'
                            ),
                            row=1, col=1
                        )
                        
                        # Top OEMs
                        if not oem_data.empty:
                            fig.add_trace(
                                go.Bar(
                                    x=oem_data['OEM'],
                                    y=oem_data['TL Base Value'],
                                    name='OEM Revenue'
                                ),
                                row=1, col=2
                            )
                        
                        # Top Partners
                        if not partner_data.empty:
                            fig.add_trace(
                                go.Bar(
                                    x=partner_data['Partner'],
                                    y=partner_data['TL Base Value'],
                                    name='Partner Revenue'
                                ),
                                row=2, col=1
                            )
                        
                        # Top Verticals
                        if not vertical_data.empty:
                            fig.add_trace(
                                go.Bar(
                                    x=vertical_data['Vertical'],
                                    y=vertical_data['TL Base Value'],
                                    name='Vertical Revenue'
                                ),
                                row=2, col=2
                            )
                        
                        fig.update_layout(
                            height=800,
                            width=1000,
                            title_text=f"Performance Dashboard for {data['person_name']}",
                            showlegend=False,
                            yaxis_tickprefix='₹',
                            yaxis_tickformat=',.2f',
                            yaxis2_tickprefix='₹',
                            yaxis2_tickformat=',.2f',
                            yaxis3_tickprefix='₹',
                            yaxis3_tickformat=',.2f',
                            yaxis4_tickprefix='₹',
                            yaxis4_tickformat=',.2f'
                        )
                        fig.show(renderer="browser")
                        return "📊 Displaying performance dashboard"

            elif query_type == 'personnel_oem':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_OEM"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.bar(filtered, x='OEM', y='TL Base Value',
                                        title=f"OEM Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying OEM performance for personnel"

            elif query_type == 'personnel_partner':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_Partner"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.bar(filtered, x='Partner', y='TL Base Value',
                                        title=f"Partner Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying partner performance for personnel"

            elif query_type == 'personnel_yearly':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_Year_Start"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.line(filtered, x='Year_Start', y='TL Base Value',
                                        title=f"Yearly Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)', 'Year_Start': 'Year'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying yearly performance for personnel"

            elif query_type == 'personnel_region':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_Region"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.bar(filtered, x='Region', y='TL Base Value',
                                        title=f"Regional Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying regional performance for personnel"

            elif query_type == 'personnel_vertical':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_Vertical"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            fig = px.bar(filtered, x='Vertical', y='TL Base Value',
                                        title=f"Vertical Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f')
                            fig.show(renderer="browser")
                            return "📊 Displaying vertical performance for personnel"

            elif query_type == 'personnel_customer':
                if data and 'person_name' in data and 'role' in data:
                    dim_key = f"{data['role']}_End Customer"
                    if dim_key in self.dimension_combinations:
                        grouped = self.dimension_combinations[dim_key]
                        filtered = grouped[grouped[data['role']] == data['person_name']]
                        
                        if not filtered.empty:
                            filtered['TL Base Value'] = filtered['TL Base Value'] / 10000000
                            # Show top 10 customers to avoid cluttered charts
                            top_customers = filtered.nlargest(10, 'TL Base Value')
                            fig = px.bar(top_customers, x='End Customer', y='TL Base Value',
                                        title=f"Top Customer Performance for {data['person_name']} (Revenue in Crores)",
                                        labels={'TL Base Value': 'Revenue (₹ Cr)'})
                            fig.update_layout(yaxis_tickprefix='₹', yaxis_tickformat=',.2f',
                                            xaxis_tickangle=-45)
                            fig.show(renderer="browser")
                            return "📊 Displaying top customer performance for personnel"

        except Exception as e:
            print(f"Could not create visualization: {e}")

def load_data_from_file(file_path):
    """Load data from Excel file"""
    try:
        df = pd.read_excel(file_path)
        print(f"📊 Data loaded successfully!")
        print(f"   • Rows: {len(df):,}")
        print(f"   • Columns: {len(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None

