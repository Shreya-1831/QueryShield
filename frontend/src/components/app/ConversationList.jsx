import { MessageSquareText } from 'lucide-react';
export default function ConversationList({items=[],onSelect}){return <div className="conversation-list">{items.map((item,i)=><button key={item.id||item.conversation_id||i} onClick={()=>onSelect?.(item)}><MessageSquareText size={16}/><span>{item.title||item.prompt||item.question||`Conversation ${i+1}`}</span></button>)}</div>;}
