import Container from '../../components/common/Container.jsx';
import SectionHeading from '../../components/common/SectionHeading.jsx';
import ContactForm from '../../components/public/ContactForm.jsx';
export default function Contact(){return <section className="page-section"><Container><SectionHeading eyebrow="CONTACT" title="Talk to the QueryShield team" description="Use this template form to prepare a local message. It does not send data externally."/><div className="contact-layout"><div><h3>Built for internal environments</h3><p className="muted">For a real deployment, connect this form to an approved internal FastAPI endpoint or support channel.</p></div><ContactForm/></div></Container></section>;}
