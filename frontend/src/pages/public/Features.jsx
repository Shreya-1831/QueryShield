import Container from '../../components/common/Container.jsx';
import SectionHeading from '../../components/common/SectionHeading.jsx';
import FeatureCard from '../../components/public/FeatureCard.jsx';
import { FEATURES } from '../../utils/constants.js';
export default function Features(){return <section className="page-section"><Container><SectionHeading eyebrow="FEATURES" title="Useful answers, with security built in" description="QueryShield combines local AI-assisted SQL generation with deterministic policy and privacy controls."/><div className="feature-grid">{FEATURES.map(f=><FeatureCard key={f.title} {...f}/>)}</div><div className="notice-card"><strong>Security note</strong><p>All identity checks, authorization, SQL validation, and privacy decisions must be enforced by the backend and database—not just the interface.</p></div></Container></section>;}
