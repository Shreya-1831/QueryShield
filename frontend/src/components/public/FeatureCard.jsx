import * as Icons from 'lucide-react';
export default function FeatureCard({icon='ShieldCheck',title,description}){const Icon=Icons[icon]||Icons.ShieldCheck;return <article className="feature-card"><div className="feature-icon"><Icon size={22}/></div><h3>{title}</h3><p>{description}</p></article>;}
