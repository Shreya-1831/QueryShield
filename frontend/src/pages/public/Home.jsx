import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, LockKeyhole, Database, BrainCircuit, EyeOff, Activity } from 'lucide-react';
import HeroSection from '../../components/public/HeroSection.jsx';
import FeatureCard from '../../components/public/FeatureCard.jsx';
import SecuritySection from '../../components/public/SecuritySection.jsx';
import WorkflowSection from '../../components/public/WorkflowSection.jsx';
import Container from '../../components/common/Container.jsx';
import SectionHeading from '../../components/common/SectionHeading.jsx';
import { FEATURES } from '../../utils/constants.js';
export default function Home(){return <><HeroSection/><section className="section"><Container><SectionHeading eyebrow="BUILT FOR TRUST" title="AI-assisted access, grounded in security" description="Make data easier to explore without treating AI output as a security boundary."/><div className="feature-grid">{FEATURES.map(f=><FeatureCard key={f.title} {...f}/>)}</div></Container></section><SecuritySection/><WorkflowSection/><section className="cta-section"><Container><div className="cta-card"><div><p className="eyebrow">YOUR INFRASTRUCTURE. YOUR CONTROL.</p><h2>Bring natural-language access to your private data.</h2><p>Explore the workspace when your local backend and approved services are configured.</p></div><Link className="button button-primary button-large" to="/access">Open Workspace <ArrowRight size={17}/></Link></div></Container></section></>;}
