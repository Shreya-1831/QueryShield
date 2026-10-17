import Container from '../../components/common/Container.jsx';
import SectionHeading from '../../components/common/SectionHeading.jsx';
import FAQAccordion from '../../components/public/FAQAccordion.jsx';
import { FAQS } from '../../utils/constants.js';
export default function FAQ(){return <section className="page-section"><Container><SectionHeading eyebrow="FAQ" title="Questions about QueryShield" description="A few essentials about deployment, security, and local AI."/><div className="narrow-content"><FAQAccordion items={FAQS}/></div></Container></section>;}
