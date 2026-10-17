import { Navigate } from 'react-router-dom';
import PublicLayout from '../layouts/PublicLayout.jsx';
import Home from '../pages/public/Home.jsx';
import Features from '../pages/public/Features.jsx';
import Security from '../pages/public/Security.jsx';
import HowItWorks from '../pages/public/HowItWorks.jsx';
import About from '../pages/public/About.jsx';
import Contact from '../pages/public/Contact.jsx';
import Documentation from '../pages/public/Documentation.jsx';
import FAQ from '../pages/public/FAQ.jsx';
import PrivacyPolicy from '../pages/public/PrivacyPolicy.jsx';
import Terms from '../pages/public/Terms.jsx';
import NotFound from '../pages/public/NotFound.jsx';
export const PublicRoutes = [{
  element:<PublicLayout/>,
  children:[
    {path:'/',element:<Home/>},
    {path:'/features',element:<Features/>},
    {path:'/security',element:<Security/>},
    {path:'/how-it-works',element:<HowItWorks/>},
    {path:'/about',element:<About/>},
    {path:'/contact',element:<Contact/>},
    {path:'/docs',element:<Documentation/>},
    {path:'/faq',element:<FAQ/>},
    {path:'/privacy',element:<PrivacyPolicy/>},
    {path:'/terms',element:<Terms/>},
    {path:'*',element:<NotFound/>},
  ]
}];
