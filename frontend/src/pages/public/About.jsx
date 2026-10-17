
import Container from '../../components/common/Container.jsx';
import SectionHeading from '../../components/common/SectionHeading.jsx';
import { Shield, Database, LockKeyhole } from 'lucide-react';

export default function About() {
  return (
    <section className="page-section">
      <Container>
        <SectionHeading
          eyebrow="ABOUT QUERYS HIELD"
          title="Private data access should be both useful and controlled"
          description="QueryShield is designed to make enterprise data easier to explore while keeping access decisions explicit and enforceable."
        />

        <div className="three-col">
          <article className="feature-card">
            <Shield />
            <h3>Security first</h3>
            <p>Identity and policy checks surround the query workflow.</p>
          </article>

          <article className="feature-card">
            <Database />
            <h3>Data stays local</h3>
            <p>Designed for internal infrastructure and local inference.</p>
          </article>

          <article className="feature-card">
            <LockKeyhole />
            <h3>Least privilege</h3>
            <p>Access should match verified identity and permitted scope.</p>
          </article>
        </div>
      </Container>
    </section>
  );
}
