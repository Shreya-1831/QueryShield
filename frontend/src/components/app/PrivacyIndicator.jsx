import { ShieldCheck, EyeOff } from 'lucide-react';
export default function PrivacyIndicator({privacy}){const text=typeof privacy==='string'?privacy:privacy?.message||privacy?.status||'Privacy controls are enforced by the backend.';return <div className="privacy-indicator"><EyeOff size={17}/><div><strong>Privacy & access controls</strong><p>{text}</p></div><ShieldCheck size={17}/></div>;}
