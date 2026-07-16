def inspect_signals(source='both',window_seconds=300,fmt='text'):
    if not 60<=window_seconds<=1800: raise ValueError('window_seconds must be between 60 and 1800')
    result={'window_seconds':window_seconds,'sources':{s:{'sample_count':0,'summary_count':0,'rssi_histogram_5dbm':{},'p10':None,'p25':None,'p50':None,'p75':None,'p90':None,'inside_threshold_crossings':0,'outside_threshold_crossings':0} for s in (('wifi','ble') if source=='both' else (source,))}}
    return result if fmt=='json' else 'no completed summaries'
