import React from 'react';
import OriginalLayout from '@theme-original/Layout';
import Footer from '@site/src/pages/_footer';

export default function Layout(props) {
  return (
    <>
      <OriginalLayout {...props} />
      <Footer />
    </>
  );
}
