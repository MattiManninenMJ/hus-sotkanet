"""Dashboard callbacks."""

from dash import Input, Output, State, callback, ALL, MATCH, html
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
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
            Output('all-indicators-data-store', 'data'),
            [Input('year-slider', 'value'),
             Input('gender-selector', 'value'),
             Input('refresh-button', 'n_clicks')],
            prevent_initial_call=False
        )
        def update_all_data(year_range, gender, n_clicks):
            """Fetch data for all indicators."""
            years = list(range(year_range[0], year_range[1] + 1))
            
            # Get all indicator IDs from metadata
            all_indicators = self.fetcher.get_all_indicators()
            indicator_ids = [int(ind_id) for ind_id in all_indicators.keys()]
            
            logger.info(f"Fetching data for {len(indicator_ids)} indicators, years: {min(years)}-{max(years)}, displaying gender: {gender}")
            
            # Fetch data for all indicators with all genders
            all_data = {}
            for ind_id in indicator_ids:
                try:
                    # IMPORTANT: Always fetch all genders for better caching and quick switching
                    all_genders = ['male', 'female', 'total']
                    logger.info(f"Fetching indicator {ind_id} with all genders: {all_genders}")
                    
                    # This should call fetch_indicator_data with all three genders
                    df = self.fetcher.fetch_indicator_data(
                        indicator_id=ind_id, 
                        years=years, 
                        genders=all_genders,
                        return_dataframe=True
                    )
                    
                    if not df.empty:
                        # Log what we got
                        logger.debug(f"Got {len(df)} total data points for indicator {ind_id}")
                        unique_genders = df['gender'].unique() if 'gender' in df.columns else []
                        logger.debug(f"Available genders in data: {list(unique_genders)}")
                        
                        # Filter by selected gender
                        df_filtered = df[df['gender'] == gender].copy()
                        
                        if not df_filtered.empty:
                            logger.debug(f"After filtering for {gender}: {len(df_filtered)} data points")
                            
                            # Sort by year to ensure proper ordering
                            df_filtered = df_filtered.sort_values('year')
                            
                            # Process data
                            df_filtered = self.processor.calculate_growth_rate(df_filtered)
                            df_filtered = self.processor.calculate_moving_average(df_filtered)
                            
                            all_data[str(ind_id)] = {
                                'data': df_filtered.to_dict('records'),
                                'years': years,
                                'gender': gender
                            }
                        else:
                            logger.warning(f"No data for indicator {ind_id} with gender {gender}")
                            all_data[str(ind_id)] = {'data': [], 'years': years, 'gender': gender}
                    else:
                        logger.warning(f"No data for indicator {ind_id} in years {min(years)}-{max(years)}")
                        # Try to get metadata to understand data availability
                        metadata = self.fetcher.get_indicator_metadata(ind_id)
                        if metadata:
                            data_range = metadata.get('range', {})
                            logger.info(f"Indicator {ind_id} data range: {data_range.get('start')}-{data_range.get('end')}")
                        all_data[str(ind_id)] = {'data': [], 'years': years, 'gender': gender}
                except Exception as e:
                    logger.error(f"Error fetching indicator {ind_id}: {e}")
                    all_data[str(ind_id)] = {'data': [], 'years': years, 'gender': gender}
            
            return all_data
        
        @app.callback(
            Output({'type': 'indicator-chart', 'index': ALL}, 'figure'),
            [Input('all-indicators-data-store', 'data'),
             Input('chart-type-selector', 'value'),
             Input('language-selector', 'value')],
            prevent_initial_call=False
        )
        def update_all_charts(stored_data, chart_type, language):
            """Update all indicator charts."""
            if not stored_data:
                # Return empty figures for all indicators
                all_indicators = self.fetcher.get_all_indicators()
                return [self._create_empty_figure("Loading...") for _ in all_indicators]
            
            figures = []
            
            # Get all indicators in sorted order to match the layout
            all_indicators = self.fetcher.get_all_indicators()
            sorted_indicators = sorted(all_indicators.items(), key=lambda x: int(x[0]))
            
            for ind_id_str, metadata in sorted_indicators:
                ind_data = stored_data.get(ind_id_str, {})
                
                if not ind_data or not ind_data.get('data'):
                    figures.append(self._create_empty_figure("No data available"))
                    continue
                
                df = pd.DataFrame(ind_data['data'])
                
                # Get title in selected language
                title = metadata.get('title', {}).get(language, 
                        metadata.get('title', {}).get('fi', f"Indicator {ind_id_str}"))
                
                # Truncate long titles for chart
                if len(title) > 80:
                    title = title[:77] + "..."
                
                # Create figure based on chart type
                fig = self._create_chart(df, title, chart_type)
                figures.append(fig)
            
            return figures
        
        @app.callback(
            Output({'type': 'info-content', 'index': MATCH}, 'children'),
            Output({'type': 'info-content', 'index': MATCH}, 'style'),
            [Input({'type': 'info-button', 'index': MATCH}, 'n_clicks'),
             Input('language-selector', 'value')],
            [State({'type': 'info-content', 'index': MATCH}, 'style'),
             State({'type': 'info-button', 'index': MATCH}, 'id')],
            prevent_initial_call=True
        )
        def toggle_info(n_clicks, language, current_style, button_id):
            """Toggle indicator information visibility."""
            if n_clicks is None:
                raise PreventUpdate
            
            # Get indicator ID from button
            ind_id = str(button_id['index'])
            
            # Toggle visibility
            if current_style is None or current_style.get('display') == 'none':
                # Show info
                metadata = self.fetcher.get_indicator_metadata(ind_id)
                
                if not metadata:
                    return html.Div("No metadata available"), {'display': 'block'}
                
                # Get organization name
                org = metadata.get('organization', {}).get('title', {}).get(language,
                      metadata.get('organization', {}).get('title', {}).get('fi', 'N/A'))
                
                # Create info content
                info_content = html.Div([
                    html.P([
                        html.Strong("Source: "),
                        html.Span(org)
                    ]),
                    html.P([
                        html.Strong("Last Updated: "),
                        html.Span(metadata.get('data-updated', 'N/A'))
                    ])
                ])
                
                return info_content, {'display': 'block'}
            else:
                # Hide info
                return html.Div(), {'display': 'none'}
        
        @app.callback(
            Output("download-all-data-csv", "data"),
            Input("download-all-button", "n_clicks"),
            State('all-indicators-data-store', 'data'),
            State('language-selector', 'value'),
            prevent_initial_call=True
        )
        def download_all_data(n_clicks, stored_data, language):
            """Download all data as CSV."""
            if not stored_data:
                return None
            
            # Combine all data into one DataFrame
            all_dfs = []
            
            for ind_id_str, ind_data in stored_data.items():
                if ind_data and ind_data.get('data'):
                    df = pd.DataFrame(ind_data['data'])
                    df['indicator_id'] = ind_id_str
                    
                    # Add indicator name
                    metadata = self.fetcher.get_indicator_metadata(ind_id_str)
                    if metadata:
                        name = metadata.get('title', {}).get(language,
                               metadata.get('title', {}).get('fi', f"Indicator {ind_id_str}"))
                        df['indicator_name'] = name
                    
                    all_dfs.append(df)
            
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                
                # Reorder columns
                cols = ['indicator_id', 'indicator_name', 'year', 'value']
                if 'absValue' in combined_df.columns:
                    cols.append('absValue')
                if 'growth_rate' in combined_df.columns:
                    cols.append('growth_rate')
                if 'gender' in combined_df.columns:
                    cols.append('gender')
                
                combined_df = combined_df[[col for col in cols if col in combined_df.columns]]
                
                # Sort by indicator and year
                combined_df = combined_df.sort_values(['indicator_id', 'year'])
                
                filename = f"hus_sotkanet_all_indicators_data.csv"
                return dict(content=combined_df.to_csv(index=False), filename=filename)
            
            return None
    
    def _create_chart(self, df: pd.DataFrame, title: str, chart_type: str) -> go.Figure:
        """Create a chart for an indicator."""
        # Ensure data is sorted by year
        df = df.sort_values('year')
        
        fig = go.Figure()
        
        if chart_type == 'line':
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=df['value'],
                mode='lines+markers',
                name='Value',
                line=dict(color='#0066CC', width=2),
                marker=dict(size=6),
                hovertemplate='Year: %{x}<br>Value: %{y:.2f}<extra></extra>'
            ))
        elif chart_type == 'bar':
            fig.add_trace(go.Bar(
                x=df['year'],
                y=df['value'],
                name='Value',
                marker_color='#0066CC',
                hovertemplate='Year: %{x}<br>Value: %{y:.2f}<extra></extra>'
            ))
        
        # Update layout with x-axis formatting
        fig.update_layout(
            title={
                'text': title,
                'font': {'size': 14},
                'x': 0,
                'xanchor': 'left'
            },
            xaxis_title="Year",
            yaxis_title="Value",
            hovermode='x unified',
            template='plotly_white',
            showlegend=False,
            height=350,
            margin=dict(l=50, r=20, t=40, b=40),
            xaxis=dict(
                tickmode='linear',
                tick0=df['year'].min(),
                dtick=1 if len(df) <= 10 else 2
            )
        )
        
        return fig
    
    def _create_empty_figure(self, message: str) -> go.Figure:
        """Create empty figure with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            template='plotly_white',
            height=350,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        return fig