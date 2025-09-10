"""Dashboard callbacks."""

from dash import Input, Output, State, callback, ALL, MATCH, html, ctx
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from .layout import DashboardLayout

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
        
        # Language update callback
        @app.callback(
            [Output('dashboard-title', 'children'),  # 0
             Output('dashboard-subtitle', 'children'),  # 1
             Output('controls-title', 'children'),  # 2
             Output('year-label', 'children'),  # 3
             Output('chart-type-label', 'children'),  # 4
             Output('chart-type-selector', 'options'),  # 5
             Output('gender-label', 'children'),  # 6
             Output('gender-selector', 'options'),  # 7
             Output('language-label', 'children'),  # 8
             Output('refresh-button', 'children'),  # 9
             Output('refresh-button', 'title'),  # 10
             Output('download-all-button', 'children'),  # 11
             Output('download-all-button', 'title'),  # 12
             Output({'type': 'indicator-title', 'index': ALL}, 'children'),  # 13
             Output('footer', 'children'),  # 14
             Output('current-language-store', 'data')],  # 15
            [Input('language-selector', 'value')],
            [State('all-indicators-data-store', 'data')],
            prevent_initial_call=False
        )
        def update_language(lang, stored_data):
            """Update all UI text based on selected language."""
            t = lambda key: DashboardLayout.get_text(key, lang)
            
            # Get all indicators metadata
            all_indicators = self.fetcher.get_all_indicators()
            sorted_indicators = sorted(all_indicators.items(), key=lambda x: int(x[0]))
            
            # Update indicator titles
            indicator_titles = []
            for ind_id_str, metadata in sorted_indicators:
                title = metadata.get('title', {}).get(lang,
                       metadata.get('title', {}).get('fi', f'Indicator {ind_id_str}'))
                if len(title) > 100:
                    title = title[:97] + "..."
                indicator_titles.append(f"[{ind_id_str}] {title}")
            
            # Create footer content
            footer_content = [
                html.Hr(),
                html.P([
                    t('footer_attribution'),
                    html.A('http://www.sotkanet.fi/', 
                          href='http://www.sotkanet.fi/',
                          target='_blank',
                          style={'color': '#0066CC'}),
                    ')'
                ], style={
                    'text-align': 'center',
                    'color': '#666',
                    'font-size': '0.9rem',
                    'margin-top': '20px',
                    'margin-bottom': '20px'
                })
            ]
            
            # Debug logging to check translation values
            logger.info(f"Language update - Selected language: {lang}")
            logger.info(f"Refresh button text: {t('refresh')}")
            logger.info(f"Refresh tooltip: {t('refresh_tooltip')}")
            logger.info(f"Download button text: {t('download')}")
            logger.info(f"Download tooltip: {t('download_tooltip')}")
            
            return [
                t('title'),  # 0: dashboard-title children
                t('subtitle'),  # 1: dashboard-subtitle children
                t('controls'),  # 2: controls-title children
                t('select_years'),  # 3: year-label children
                t('chart_type'),  # 4: chart-type-label children
                [  # 5: chart-type-selector options
                    {'label': t('line_chart'), 'value': 'line'},
                    {'label': t('bar_chart'), 'value': 'bar'}
                ],
                t('gender'),  # 6: gender-label children
                [  # 7: gender-selector options
                    {'label': t('total'), 'value': 'total'},
                    {'label': t('male'), 'value': 'male'},
                    {'label': t('female'), 'value': 'female'}
                ],
                t('language'),  # 8: language-label children
                t('refresh'),  # 9: refresh-button children (button text)
                t('refresh_tooltip'),  # 10: refresh-button title (tooltip)
                t('download'),  # 11: download-all-button children (button text)
                t('download_tooltip'),  # 12: download-all-button title (tooltip)
                indicator_titles,  # 13: indicator-title children
                footer_content,  # 14: footer children
                lang  # 15: current-language-store data
            ]
        
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
             Input('current-language-store', 'data')],
            prevent_initial_call=False
        )
        def update_all_charts(stored_data, chart_type, language):
            """Update all indicator charts."""
            # Get translations for chart labels
            t = lambda key: DashboardLayout.get_text(key, language)
            
            if not stored_data:
                # Return empty figures for all indicators
                all_indicators = self.fetcher.get_all_indicators()
                return [self._create_empty_figure(t('loading')) for _ in all_indicators]
            
            figures = []
            
            # Get all indicators in sorted order to match the layout
            all_indicators = self.fetcher.get_all_indicators()
            sorted_indicators = sorted(all_indicators.items(), key=lambda x: int(x[0]))
            
            for ind_id_str, metadata in sorted_indicators:
                ind_data = stored_data.get(ind_id_str, {})
                
                if not ind_data or not ind_data.get('data'):
                    figures.append(self._create_empty_figure(t('no_data')))
                    continue
                
                df = pd.DataFrame(ind_data['data'])
                
                # Get title in selected language
                title = metadata.get('title', {}).get(language, 
                        metadata.get('title', {}).get('fi', f"Indicator {ind_id_str}"))
                
                # Truncate long titles for chart
                if len(title) > 80:
                    title = title[:77] + "..."
                
                # Get unit from metadata if available
                unit = self._extract_unit(metadata, language)
                
                # Create figure based on chart type
                fig = self._create_chart(df, title, chart_type, unit, language)
                figures.append(fig)
            
            return figures
        
        @app.callback(
            Output({'type': 'info-content', 'index': MATCH}, 'children'),
            Output({'type': 'info-content', 'index': MATCH}, 'style'),
            [Input({'type': 'info-button', 'index': MATCH}, 'n_clicks'),
             Input('current-language-store', 'data')],
            [State({'type': 'info-button', 'index': MATCH}, 'id'),
             State({'type': 'info-content', 'index': MATCH}, 'style')],
            prevent_initial_call=True
        )
        def toggle_info(n_clicks, language, button_id, current_style):
            """Toggle indicator information visibility."""
            # Get indicator ID from button
            ind_id = str(button_id['index'])
            
            # Check what triggered the callback
            triggered_prop = ctx.triggered[0]['prop_id'] if ctx.triggered else None
            
            # Determine if this is a button click or language change
            is_button_click = 'info-button' in str(triggered_prop) if triggered_prop else False
            is_language_change = 'current-language-store' in str(triggered_prop) if triggered_prop else False
            
            # Get translations
            t = lambda key: DashboardLayout.get_text(key, language)
            
            # Handle button click - toggle visibility
            if is_button_click:
                if current_style and current_style.get('display') == 'block':
                    # Panel is open, close it
                    return html.Div(), {'display': 'none'}
                else:
                    # Panel is closed, open it
                    metadata = self.fetcher.get_indicator_metadata(ind_id)
                    
                    if not metadata:
                        return html.Div(t('no_metadata')), {'display': 'block'}
                    
                    # Create content
                    content = self._create_info_content(metadata, language, t)
                    return content, {'display': 'block'}
            
            # Handle language change - only update content if panel is already open
            elif is_language_change:
                if current_style and current_style.get('display') == 'block':
                    # Panel is open, update content but keep it open
                    metadata = self.fetcher.get_indicator_metadata(ind_id)
                    
                    if not metadata:
                        return html.Div(t('no_metadata')), {'display': 'block'}
                    
                    content = self._create_info_content(metadata, language, t)
                    return content, {'display': 'block'}
                else:
                    # Panel is closed, keep it closed
                    raise PreventUpdate
            
            # Default case
            raise PreventUpdate
        
        def _create_info_content(self, metadata, language, t):
            """Helper method to create info content."""
            # Get organization name in selected language
            org = metadata.get('organization', {}).get('title', {}).get(language,
                  metadata.get('organization', {}).get('title', {}).get('fi', 'N/A'))
            
            # Get description if available
            description = metadata.get('description', {}).get(language,
                         metadata.get('description', {}).get('fi', ''))
            
            # Create info content as a list of components
            info_content = []
            
            # Add description if available - parse HTML content
            if description:
                description_cleaned = self._parse_html_description(description)
                info_content.append(description_cleaned)
            
            # Add source and last updated info
            info_content.extend([
                html.P([
                    html.Strong(f"{t('source')} "),
                    html.Span(org)
                ]),
                html.P([
                    html.Strong(f"{t('last_updated')} "),
                    html.Span(metadata.get('data-updated', 'N/A'))
                ])
            ])
            
            return html.Div(info_content)
        
        @app.callback(
            Output("download-all-data-csv", "data"),
            Input("download-all-button", "n_clicks"),
            State('all-indicators-data-store', 'data'),
            State('current-language-store', 'data'),
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
                    
                    # Skip empty DataFrames to avoid FutureWarning
                    if df.empty:
                        continue
                    
                    df['indicator_id'] = ind_id_str
                    
                    # Add indicator name in selected language
                    metadata = self.fetcher.get_indicator_metadata(ind_id_str)
                    if metadata:
                        name = metadata.get('title', {}).get(language,
                               metadata.get('title', {}).get('fi', f"Indicator {ind_id_str}"))
                        df['indicator_name'] = name
                    
                    all_dfs.append(df)
            
            # Only proceed if we have non-empty DataFrames
            if all_dfs:
                # Filter out any remaining empty DataFrames
                all_dfs = [df for df in all_dfs if not df.empty]
                
                if not all_dfs:
                    return None
                
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
    
    def _create_info_content(self, metadata, language, t):
        """Helper method to create info content."""
        # Get organization name in selected language
        org = metadata.get('organization', {}).get('title', {}).get(language,
              metadata.get('organization', {}).get('title', {}).get('fi', 'N/A'))
        
        # Get description if available
        description = metadata.get('description', {}).get(language,
                     metadata.get('description', {}).get('fi', ''))
        
        # Create info content as a list of components
        info_content = []
        
        # Add description if available - parse HTML content
        if description:
            description_cleaned = self._parse_html_description(description)
            info_content.append(description_cleaned)
        
        # Add source and last updated info
        info_content.extend([
            html.P([
                html.Strong(f"{t('source')} "),
                html.Span(org)
            ]),
            html.P([
                html.Strong(f"{t('last_updated')} "),
                html.Span(metadata.get('data-updated', 'N/A'))
            ])
        ])
        
        return html.Div(info_content)
    
    def _parse_html_description(self, description: str) -> html.Div:
        """
        Parse HTML description and convert to Dash components.
        
        Args:
            description: HTML string with description
            
        Returns:
            Dash HTML component
        """
        if not description:
            return html.Div()
        
        # Remove leading/trailing asterisks that wrap the entire content
        description = description.strip()
        if description.startswith('*') and description.endswith('*'):
            description = description[1:-1]
        
        # Remove any remaining asterisks
        description = description.replace('*', '')
        
        # Replace multiple <br> tags with paragraph breaks
        description = re.sub(r'(<br\s*/?>)+', '\n\n', description)
        
        # Split by <p> tags first
        parts = re.split(r'<p[^>]*>', description)
        
        elements = []
        
        for part in parts:
            # Remove closing </p> tags
            part = part.replace('</p>', '')
            part = part.strip()
            
            if not part:
                continue
            
            # Split by double newlines (from <br> replacements) to create paragraphs
            sub_paragraphs = part.split('\n\n')
            
            for para in sub_paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Handle bold text marked with **
                if '**' in para:
                    parts = para.split('**')
                    para_content = []
                    for i, text_part in enumerate(parts):
                        if i % 2 == 1:  # Odd indices are bold
                            para_content.append(html.Strong(text_part))
                        elif text_part:  # Even indices are normal text
                            para_content.append(text_part)
                    elements.append(html.P(para_content, style={'margin-bottom': '10px'}))
                else:
                    # Regular paragraph
                    elements.append(html.P(para, style={'margin-bottom': '10px'}))
        
        # If no elements were created, just return the text as-is in a paragraph
        if not elements and description.strip():
            # Final cleanup - remove any remaining HTML tags
            clean_text = re.sub(r'<[^>]+>', '', description)
            elements.append(html.P(clean_text, style={'margin-bottom': '10px'}))
        
        return html.Div(elements, style={'font-style': 'italic', 'margin-bottom': '15px'})
    
    def _extract_unit(self, metadata: Dict, language: str) -> str:
        """Extract unit from metadata."""
        # Check if there's a unit field
        if 'unit' in metadata:
            unit = metadata['unit']
            if isinstance(unit, dict):
                return unit.get(language, unit.get('fi', ''))
            return str(unit)
        
        # Try to extract from title
        title = metadata.get('title', {}).get(language,
                metadata.get('title', {}).get('fi', ''))
        if '/ 100 000' in title:
            return '/ 100 000'
        elif '/ 1 000' in title:
            return '/ 1 000'
        elif '%' in title:
            return '%'
        
        return ''
    
    def _create_chart(self, df: pd.DataFrame, title: str, chart_type: str, 
                     unit: str = '', language: str = 'fi') -> go.Figure:
        """Create a chart for an indicator."""
        # Ensure data is sorted by year
        df = df.sort_values('year')
        
        # Get axis labels based on language
        axis_labels = {
            'fi': {'year': 'Vuosi', 'value': 'Arvo'},
            'sv': {'year': 'År', 'value': 'Värde'},
            'en': {'year': 'Year', 'value': 'Value'}
        }
        
        labels = axis_labels.get(language, axis_labels['fi'])
        
        # Add unit to y-axis label if available
        y_label = labels['value']
        if unit:
            y_label = f"{labels['value']} ({unit})"
        
        fig = go.Figure()
        
        if chart_type == 'line':
            fig.add_trace(go.Scatter(
                x=df['year'],
                y=df['value'],
                mode='lines+markers',
                name=labels['value'],
                line=dict(color='#0066CC', width=2),
                marker=dict(size=6),
                hovertemplate=f"{labels['year']}: %{{x}}<br>{labels['value']}: %{{y:.2f}}<extra></extra>"
            ))
        elif chart_type == 'bar':
            fig.add_trace(go.Bar(
                x=df['year'],
                y=df['value'],
                name=labels['value'],
                marker_color='#0066CC',
                hovertemplate=f"{labels['year']}: %{{x}}<br>{labels['value']}: %{{y:.2f}}<extra></extra>"
            ))
        
        # Update layout with x-axis formatting
        fig.update_layout(
            title={
                'text': title,
                'font': {'size': 14},
                'x': 0,
                'xanchor': 'left'
            },
            xaxis_title=labels['year'],
            yaxis_title=y_label,
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