/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import React from 'react';
import Translate, {translate} from '@docusaurus/Translate';
import {useDocsSidebar} from '@docusaurus/theme-common/internal';
import PaginatorNavLink from '@theme/PaginatorNavLink';

// Helper function to get the translated title from sidebar items
function getTranslatedTitle(permalink, sidebarItems) {
  if (!sidebarItems) {
    return null;
  }

  for (const item of sidebarItems) {
    if (item.type === 'doc' && item.href === permalink) {
      return item.label;
    } else if (item.type === 'category' && item.items) {
      const translatedTitle = getTranslatedTitle(permalink, item.items);
      if (translatedTitle) {
        return translatedTitle;
      }
    }
  }

  return null;
}

export default function DocPaginator(props) {
  const {previous, next} = props;
  const sidebar = useDocsSidebar();
  const sidebarItems = sidebar?.items || [];

  // Try to get translated titles from sidebar
  const previousTranslatedTitle = previous && getTranslatedTitle(previous.permalink, sidebarItems);
  const nextTranslatedTitle = next && getTranslatedTitle(next.permalink, sidebarItems);

  return (
    <nav
      className="pagination-nav docusaurus-mt-lg"
      aria-label={translate({
        id: 'theme.docs.paginator.navAriaLabel',
        message: 'Docs pages',
        description: 'The ARIA label for the docs pagination',
      })}>
      {previous && (
        <PaginatorNavLink
          {...previous}
          title={previousTranslatedTitle || previous.title}
          subLabel={
            <Translate
              id="theme.docs.paginator.previous"
              description="The label used to navigate to the previous doc">
              Previous
            </Translate>
          }
        />
      )}
      {next && (
        <PaginatorNavLink
          {...next}
          title={nextTranslatedTitle || next.title}
          subLabel={
            <Translate
              id="theme.docs.paginator.next"
              description="The label used to navigate to the next doc">
              Next
            </Translate>
          }
          isNext
        />
      )}
    </nav>
  );
}