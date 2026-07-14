import ray

context = ray.init(include_dashboard=True)
if context.dashboard_url:
    print(f"Dashboard URL: {context.dashboard_url}")
else:
    print("Dashboard URL is not available. Ensure that the Ray dashboard is enabled and running.")
    ray.shutdown()

# Get and print the cluster resources
cluster_resources = ray.cluster_resources()
print("\nCluster Resources:")
for resource, value in cluster_resources.items():
    print(f"{resource}: {value}")