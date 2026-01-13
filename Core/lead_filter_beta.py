# Core/lead_filter.py
import pandas as pd
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

def filter_attractive_leads_beta(df_leads: pd.DataFrame, df_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Filters for the most attractive leads and prepares the data for reporting.

    Args:
        df_leads (pd.DataFrame): DataFrame containing the latest leads with metrics.
        df_metrics (pd.DataFrame): DataFrame containing market metrics per model.

    Returns:
        pd.DataFrame: A raw DataFrame with attractive leads and calculated opportunity metrics.
    """
    logger.info(f"LEAD_FILTER_BETA: Iniciando el filtrado de leads atractivos. Leads de entrada: {len(df_leads)}")

    if df_leads.empty:
        return pd.DataFrame()

    # Price filter
    attractive_leads = df_leads[df_leads['Price'] < df_leads['mean_price']].copy()
    logger.info(f"LEAD_FILTER_BETA: Se encontraron {len(attractive_leads)} leads atractivos después de filtrar por precio.")

    if attractive_leads.empty: return pd.DataFrame()

    # Calculate Opportunity Indicator
    attractive_leads['Oportunidad_Precio'] = (attractive_leads['Price'] - attractive_leads['mean_price']) / attractive_leads['mean_price']
    
    # Ensure Kilometers column exists
    if 'Kilometers' not in attractive_leads.columns:
        if 'kilometers' in attractive_leads.columns:
            attractive_leads.rename(columns={'kilometers': 'Kilometers'}, inplace=True)
        else:
            attractive_leads['Kilometers'] = 'N/A'

    return attractive_leads