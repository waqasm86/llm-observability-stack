# Monitoring layer

This umbrella chart pins kube-prometheus-stack 86.2.3, prometheus-blackbox-exporter
11.12.0, and prometheus-pushgateway 3.6.1.

Run helm dependency build monitoring, then install the chart in the monitoring namespace.
After its CRDs are ready, enable monitoring.enabled in the application chart.

The local defaults retain Prometheus data for three days, persist Prometheus, Alertmanager,
and Grafana using the k3s local-path storage class, and discover monitoring resources across
namespaces. Tune retention and storage for a production or multi-node cluster.
