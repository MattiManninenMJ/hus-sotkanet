"""Dashboard callbacks."""

from dash import Input, Output, State, callback, dcc, html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger('dashboard.callbacks')


class DashboardCallbacks:
    """Manages dashboard callbacks."""
    
    def __init__(self, data_fetcher, data_processor):
        """
        Initialize callbacks with data handlers.
        
        Args:
            data_fetcher: SotkanetDataFetcher instance
            data_processor: DataProcessor instance
        """
        self.fetcher = data_fetcher
        self.processor = data_processor
    
    def register_callbacks(self, app):
        """Register all callbacks with the app."""
        
        @app.callback(
            Output('indicator-data-store', 'data'),
            [Input('indicator-selector', 'value'),
             Input('year-slider', 'value'),
             Input('refresh-button', 'n_clicks')]
        )
        def update_data_store(indicator_id, year_range, n_clicks):
            """Fetch and store indicator data."""
            if not indicator_id:
                return {}
            
            years = list(range(year_range[0], year_range[1] + 1))
            df = self.fetcher.fetch_indicator_data(int(indicator_id), years)
            
            if df.empty:
                logger.warning(f"No data retrieved for indicator {indicator_id}")
                return {}
            
            # Process data
            df = self.processor.calculate_growth_rate(df)
            df = self.processor.calculate_moving_average(df)
            stats = self.processor.calculate_statistics(df)
            
            return {
                'indicator_id': indicator_id,
                'years': years,
                'data': df.to_dict('records'),
                'statistics': stats
            }
        
        @app.callback(
            Output('indicator-info-content', 'children'),
            Input('indicator-selector', 'value')
        )
        def update_indicator_info(indicator_id):
            """Update indicator information card."""
            if not indicator_id:
                return html.Div("Select an indicator", className="info-message")
            
            info = self.fetcher.get_indicator_metadata(str(indicator_id))
            
            if not info:
                return html.Div("No metadata available", className="info-message")
            
            title = info.get('title', {})
            
            return html.Div([
                html.H4("Indicator Information"),
                html.Div([
                    html.P([
                        html.Strong("Finnish: "),
                        html.Span(title.get('fi', 'N/A'))
                    ]),
                    html.P([
                        html.Strong("English: "),
                        html.Span(title.get('en', 'N/A'))
                    ]),
                    html.P([
                        html.Strong("Swedish: "),
                        html.Span(title.get('sv', 'N/A'))
                    ]),
                    html.Hr(),
                    html.P([
                        html.Strong("Organization: "),
                        html.Span(info.get('organization', {}).get('title', {}).get('fi', 'N/A'))
                    ]),
                    html.P([
                        html.Strong("Last Updated: "),
                        html.Span(info.get('data-updated', 'N/A'))
                    ]),
                    html.P([
                        html.Strong("Decimals: "),
                        html.Span(str(info.get('decimals', 1)))
                    ])
                ])
            ])
        
        @app.callback(
            Output('main-chart', 'figure'),
            [Input('indicator-data-store', 'data'),
             Input('chart-type-selector', 'value'),
             Input('options-checklist', 'value')]
        )
        def update_main_chart(stored_data, chart_type, options):
            """Update main chart."""
            if not stored_data or 'data' not in stored_data:
                return self._create_empty_figure("No data available")
            
            df = pd.DataFrame(stored_data['data'])
            info = self.fetcher.get_indicator_metadata(stored_data['indicator_id'])
            title = info.get('title', {}).get('fi', f"Indicator {stored_data['indicator_id']}")
            
            fig = go.Figure()
            
            # Main data trace
            if chart_type == 'line':
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['value'],
                    mode='lines+markers',
                    name='Value',
                    line=dict(color='#0066CC', width=2),
                    marker=dict(size=8)
                ))
            elif chart_type == 'bar':
                fig.add_trace(go.Bar(
                    x=df['year'],
                    y=df['value'],
                    name='Value',
                    marker_color='#00AA88'
                ))
            elif chart_type == 'area':
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['value'],
                    mode='lines',
                    name='Value',
                    fill='tozeroy',
                    line=dict(color='#0066CC')
                ))
            elif chart_type == 'scatter':
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['value'],
                    mode='markers',
                    name='Value',
                    marker=dict(size=10, color='#0066CC')
                ))
            
            # Add optional features
            if options and 'moving_avg' in options and 'moving_avg' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['moving_avg'],
                    mode='lines',
                    name='3-Year Moving Avg',
                    line=dict(color='orange', dash='dash')
                ))
            
            if options and 'trend' in options:
                # Add trend line
                z = np.polyfit(df['year'], df['value'], 1)
                p = np.poly1d(z)
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=p(df['year']),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', dash='dot')
                ))
            
            if options and 'outliers' in options:
                df_outliers = self.processor.detect_outliers(df)
                outliers = df_outliers[df_outliers['is_outlier']]
                if not outliers.empty:
                    fig.add_trace(go.Scatter(
                        x=outliers['year'],
                        y=outliers['value'],
                        mode='markers',
                        name='Outliers',
                        marker=dict(size=12, color='red', symbol='x')
                    ))
            
            # Update layout
            fig.update_layout(
                title=title[:80],
                xaxis_title="Year",
                yaxis_title="Value",
                hovermode='x unified',
                template='plotly_white',
                showlegend=True,
                height=400
            )
            
            return fig
        
        @app.callback(
            Output('statistics-content', 'children'),
            Input('indicator-data-store', 'data')
        )
        def update_statistics(stored_data):
            """Update statistics cards."""
            if not stored_data or 'statistics' not in stored_data:
                return html.Div("No statistics available", className="statistics-empty")
            
            stats = stored_data['statistics']
            
            # Determine trend class
            if stats['trend_pct'] is not None:
                if stats['trend_pct'] > 0:
                    trend_class = "trend-up"
                    trend_icon = "↑"
                elif stats['trend_pct'] < 0:
                    trend_class = "trend-down"
                    trend_icon = "↓"
                else:
                    trend_class = "trend-neutral"
                    trend_icon = "→"
                trend_text = f"{trend_icon} {stats['trend_pct']:+.1f}%"
            else:
                trend_text = "N/A"
                trend_class = "trend-neutral"
            
            return html.Div([
                html.Div([
                    html.H4("Latest Value"),
                    html.P(f"{stats['latest_value']:.1f}", className="stat-value"),
                    html.P(f"Year: {stats['latest_year']}", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.H4("Trend"),
                    html.P(trend_text, className=f"stat-value {trend_class}"),
                    html.P("Year-over-year", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.H4("Average"),
                    html.P(f"{stats['mean_value']:.1f}", className="stat-value"),
                    html.P(f"σ = {stats['std_value']:.2f}", className="stat-label")
                ], className="stat-card"),
                
                html.Div([
                    html.H4("Range"),
                    html.P(f"{stats['min_value']:.1f} - {stats['max_value']:.1f}", 
                          className="stat-value"),
                    html.P("Min - Max", className="stat-label")
                ], className="stat-card"),
            ])
        
        @app.callback(
            Output('data-table-content', 'children'),
            Input('indicator-data-store', 'data')
        )
        def update_data_table(stored_data):
            """Update data table."""
            if not stored_data or 'data' not in stored_data:
                return html.Div("No data to display", className="table-empty")
            
            df = pd.DataFrame(stored_data['data'])
            
            # Select columns to display
            columns_to_show = ['year', 'value', 'absValue']
            if 'growth_rate' in df.columns:
                columns_to_show.append('growth_rate')
            
            df_display = df[columns_to_show].copy()
            
            # Format columns
            if 'growth_rate' in df_display.columns:
                df_display['growth_rate'] = df_display['growth_rate'].apply(
                    lambda x: f"{x:+.1f}%" if pd.notna(x) else "-"
                )
            
            return html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Year"),
                        html.Th("Value"),
                        html.Th("Absolute Value"),
                        html.Th("Growth Rate") if 'growth_rate' in columns_to_show else None
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(row['year']),
                        html.Td(f"{row['value']:.2f}"),
                        html.Td(f"{row.get('absValue', 'N/A')}"),
                        html.Td(row.get('growth_rate', '')) if 'growth_rate' in columns_to_show else None
                    ]) for _, row in df_display.iterrows()
                ])
            ], className="data-table")
        
        @app.callback(
            Output("download-dataframe-csv", "data"),
            Input("download-button", "n_clicks"),
            State('indicator-data-store', 'data'),
            prevent_initial_call=True
        )
        def download_data(n_clicks, stored_data):
            """Download data as CSV."""
            if not stored_data or 'data' not in stored_data:
                return None
            
            df = pd.DataFrame(stored_data['data'])
            info = self.fetcher.get_indicator_metadata(stored_data['indicator_id'])
            filename = f"indicator_{stored_data['indicator_id']}_data.csv"
            
            # Use dict format for download
            return dict(content=df.to_csv(index=False), filename=filename)
    
    def _create_empty_figure(self, message: str) -> go.Figure:
        """Create empty figure with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white',
            height=400
        )
        return fig