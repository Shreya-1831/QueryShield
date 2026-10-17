import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
export default function FAQAccordion({items=[]}){const [active,setActive]=useState(0);return <div className="faq-list">{items.map((item,i)=><section className={`faq-item ${active===i?'faq-active':''}`} key={item.question}><button onClick={()=>setActive(active===i?-1:i)} aria-expanded={active===i}><span>{item.question}</span><ChevronDown size={18}/></button>{active===i&&<p>{item.answer}</p>}</section>)}</div>;}
