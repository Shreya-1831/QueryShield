export const APP_NAME = 'QueryShield';
export const NAV_LINKS = [
  {label:'Features',to:'/features'},
  {label:'Security',to:'/security'},
  {label:'How it works',to:'/how-it-works'},
  {label:'About',to:'/about'},
  {label:'Contact',to:'/contact'},
];
export const FEATURES = [
  {icon:'ShieldCheck',title:'Identity-aware access',description:'Resolve trusted Windows identity and role before permitting database access.'},
  {icon:'LockKeyhole',title:'Least-privilege controls',description:'Apply role-aware database access and row/column authorization.'},
  {icon:'ScanSearch',title:'SQL security gateway',description:'Validate generated SQL and reject unsafe or non-read operations.'},
  {icon:'BrainCircuit',title:'Local AI inference',description:'Generate candidate SQL with a locally hosted model, without a cloud AI dependency at runtime.'},
  {icon:'EyeOff',title:'Privacy filtering',description:'Inspect results and mask sensitive information before display.'},
  {icon:'ClipboardList',title:'Auditing and monitoring',description:'Track security decisions and monitor system health.'},
];
export const WORKFLOW = [
  'Windows identity','Role resolution','Database authentication','Policy evaluation',
  'Local AI SQL generation','SQL validation','Authorized results'
];
export const FAQS = [
  {question:'Does QueryShield send my database data to a cloud AI provider?',answer:'The intended deployment uses a locally hosted Ollama model and on-premise services. Configure and verify all runtime integrations before production.'},
  {question:'Can employees run write queries?',answer:'No. The intended query workflow is read-only and must reject non-SELECT statements on the backend.'},
  {question:'Does hiding an Admin page secure it?',answer:'No. Frontend route guards improve the user experience, but every privileged action must be authorized by FastAPI.'},
  {question:'Can QueryShield run without internet access?',answer:'It is designed for offline/on-premise runtime when required packages, assets, database services, and approved local models are already installed.'},
];
