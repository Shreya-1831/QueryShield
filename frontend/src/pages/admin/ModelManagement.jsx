
import { useEffect, useState } from 'react';
import PageHeader from '../../components/common/PageHeader.jsx';
import { getModels } from '../../services/adminService.js';
import Loader from '../../components/common/Loader.jsx';
import ErrorState from '../../components/common/ErrorState.jsx';
import EmptyState from '../../components/common/EmptyState.jsx';

export default function ModelManagement() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');

    try {
      const data = await getModels();
      setModels(
        Array.isArray(data) ? data : data.models ?? data.items ?? []
      );
    } catch (e) {
      setError(
        e.userMessage || e.message || 'Model endpoint unavailable.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="LOCAL AI"
        title="Model management"
        description="Inspect approved local models exposed by your backend. This page does not download or switch models."
      />

      {loading ? (
        <Loader />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : models.length ? (
        <div className="model-grid">
          {models.map((model, index) => (
            <article
              className="panel"
              key={model.model_id ?? model.model_name ?? index}
            >
              <h3>
                {model.model_name ?? 'Unknown model'}
                {model.version != null && `:${model.version}`}
              </h3>

              <p className="muted">
                Status: {model.status ?? 'Not provided'}
              </p>

              <p className="muted">
                Approval: {model.approved ? 'Approved' : 'Not approved'}
              </p>

              {model.avg_latency_ms != null && (
                <p className="muted">
                  Average latency: {model.avg_latency_ms} ms
                </p>
              )}
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No model data returned"
          description="Verify the local model registry in the backend."
        />
      )}
    </>
  );
}
