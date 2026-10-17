import { AlertTriangle, RefreshCw } from 'lucide-react';
export default function ErrorState({title='Unable to load data',message='Please try again.',onRetry}){return <div className="state-card"><AlertTriangle size={28}/><h3>{title}</h3><p>{message}</p>{onRetry&&<button className="button button-secondary" onClick={onRetry}><RefreshCw size={16}/> Try again</button>}</div>;}
