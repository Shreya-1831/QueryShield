import { LoaderCircle } from 'lucide-react';
export default function Loader({full=false,label='Loading…'}){return <div className={`loader ${full?'loader-full':''}`} role="status"><LoaderCircle className="spin" size={22}/><span>{label}</span></div>;}
