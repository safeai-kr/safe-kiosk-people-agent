from __future__ import annotations
from ..domain import ClassificationLabel, ClassificationState, ClassificationUpdate, ProtocolThresholds
class RssiClassifier:
    def __init__(self,thresholds:ProtocolThresholds):self.thresholds=thresholds;self.state=ClassificationState(ClassificationLabel.UNKNOWN,None,0,(),None)
    def update(self,observed_at,rssi_dbm:int)->ClassificationUpdate:
        label=ClassificationLabel.INSIDE if rssi_dbm>=self.thresholds.inside_rssi_dbm else ClassificationLabel.OUTSIDE if rssi_dbm<=self.thresholds.outside_rssi_dbm else ClassificationLabel.UNKNOWN
        previous=self.state.confirmed; changed=label!=previous and label!=ClassificationLabel.UNKNOWN
        if changed:self.state=ClassificationState(label,None,0,(),observed_at)
        return ClassificationUpdate(previous,self.state.confirmed,changed,rssi_dbm,observed_at,self.state)
