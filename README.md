# kubanetics

A container with various scripts for Kubernetes

## Usage

### fstrim

```yaml
env:
  - name: SCRIPT_NAME
    value: fstrim.sh
```

### talos-suc

```yaml
env:
  - name: SCRIPT_NAME
    value: talos-upgrade.sh
  - name: SETTLE_DOWN_SECONDS
    value: "10"
  - name: TALOS_HEALTHCHECK
    value: "true"
  - name: TALOS_TIMEOUT
    value: "600s"
  - name: ROOK_CEPH_HEALTHCHECK
    value: "true"
  - name: ROOK_CEPH_TIMEOUT
    value: "600s"
  - name: CNPG_MAINTENANCE
    value: "true"
```