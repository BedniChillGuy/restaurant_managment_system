#!/bin/bash
# Скрипт для удаления всех ресурсов

echo "⚠️  This will delete all Restaurant Management System resources from Kubernetes"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo "Deleting all resources..."
kubectl delete namespace restaurant

echo ""
echo "✅ All resources deleted"
echo ""
echo "To verify:"
echo "  kubectl get all -n restaurant"

