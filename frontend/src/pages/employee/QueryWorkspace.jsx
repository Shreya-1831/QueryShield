
import PageHeader from '../../components/common/PageHeader.jsx';
import QueryEditor from '../../components/app/QueryEditor.jsx';
import SQLPreview from '../../components/app/SQLPreview.jsx';
import ResultTable from '../../components/app/ResultTable.jsx';
import ResultChart from '../../components/app/ResultChart.jsx';
import PrivacyIndicator from '../../components/app/PrivacyIndicator.jsx';
import useQuery from '../../hooks/useQuery.js';
import useNotifications from '../../hooks/useNotifications.js';

export default function QueryWorkspace() {
  const { loading, result, error, run } = useQuery();
  const { notify } = useNotifications();

  async function submit(prompt) {
    try {
      const r = await run(prompt);

      if (r?.success === false) {
        notify(
          r.reason || r.response || 'The request was not approved.',
          'error'
        );
      } else {
        notify('Query request processed by the backend.', 'success');
      }
    } catch (e) {
      notify(
        e.userMessage || e.message || 'Query failed.',
        'error'
      );
    }
  }

  const data = result?.data;
  const visualization = result?.visualization;

  return (
    <>
      <PageHeader
        eyebrow="NATURAL LANGUAGE TO SQL"
        title="AI Query Workspace"
        description="Ask a question in plain language. The backend must validate and authorize the query before execution."
      />

      <QueryEditor onSubmit={submit} loading={loading} />

      {error && <div className="inline-alert">{error}</div>}

      {result && (
        <div className="result-stack">
          {result.response && (
            <section className="panel">
              <h3>Response</h3>
              <p>{result.response}</p>
            </section>
          )}

          {result.reason && (
            <div className="notice-card">
              <strong>{result.stage || 'Request status'}</strong>
              <p>{result.reason}</p>

              {result.safe_alternative && (
                <p>Safe alternative: {result.safe_alternative}</p>
              )}
            </div>
          )}

          <PrivacyIndicator privacy={result.privacy} />

          {result.sql && <SQLPreview sql={result.sql} />}

          {Array.isArray(data) && data.length > 0 && (
            <>
              {visualization?.type !== 'table' && (
                <ResultChart
                  data={visualization?.data ?? data}
                  visualization={visualization}
                />
              )}

              <ResultTable data={data} />
            </>
          )}
        </div>
      )}
    </>
  );
}
