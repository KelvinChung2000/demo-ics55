# Zoom to [T0, T1] (dump time units) and drop a marker at MARK if set.
gtkwave::setZoomRangeTimes $env(T0) $env(T1)
if {[info exists env(MARK)]} { gtkwave::setMarker $env(MARK) }
