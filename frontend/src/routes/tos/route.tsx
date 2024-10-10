import { json } from "@remix-run/react";
import {
  Section,
  Paragraph,
  Bold,
  OrderedList,
  Mailto,
  ExternalLink,
} from "./custom-elements";

export const clientLoader = () => {
  const mode = import.meta.env.VITE_APP_MODE || "oss";

  if (mode !== "saas") {
    // eslint-disable-next-line @typescript-eslint/no-throw-literal
    throw json(null, { status: 404 });
  }

  return json(null);
};

function TOS() {
  return (
    <main className="flex flex-col items-center px-80 py-10 gap-10">
      <h1 className="text-4xl">Terms of Service</h1>

      <Section title="Acceptance of These Terms of Service">
        <Paragraph>
          All Hands AI (“All Hands AI”, “we,” “us,” or “our”) provides our
          services (described below) and related content to you through our
          website(s) located at{" "}
          <ExternalLink>https://www.all-hands.dev/</ExternalLink> (the
          “Service”). All access and use of the Service is subject to the terms
          and conditions contained in these Terms of Service (as amended from
          time to time, these “Terms of Service”). By accessing, browsing, or
          otherwise using the Service, you acknowledge that you have read,
          understood, and agree to be bound by these Terms of Service. If you do
          not accept the terms and conditions of these Terms of Service, you
          will not access, browse, or otherwise use the Service.
        </Paragraph>
        <Paragraph>
          We reserve the right, at our sole discretion, to change or modify
          portions of these Terms of Service at any time. If we do this, we will
          post the changes on this page and will indicate at the top of this
          page the date these Terms of Service were last revised. You may read a
          current, effective copy of these Terms of Service by visiting the
          “Terms of Service” link on the Service. We will also notify you of any
          material changes, either through the Service user interface, a pop-up
          notice, email, or through other reasonable means. Your continued use
          of the Service after the date any such changes become effective
          constitutes your acceptance of the new Terms of Service. You should
          periodically visit this page to review the current Terms of Service so
          you are aware of any revisions. If you do not agree to abide by these
          or any future Terms of Service, you will not access, browse, or use
          (or continue to access, browse, or use) the Service.
        </Paragraph>
        <Paragraph bold italic>
          PLEASE READ THESE TERMS OF SERVICE CAREFULLY, AS THEY CONTAIN AN
          AGREEMENT TO ARBITRATE AND OTHER IMPORTANT INFORMATION REGARDING YOUR
          LEGAL RIGHTS, REMEDIES, AND OBLIGATIONS. THE AGREEMENT TO ARBITRATE
          REQUIRES (WITH LIMITED EXCEPTION) THAT YOU SUBMIT CLAIMS YOU HAVE
          AGAINST US TO BINDING AND FINAL ARBITRATION, AND FURTHER (1) YOU WILL
          ONLY BE PERMITTED TO PURSUE CLAIMS AGAINST ALL HANDS AI ON AN
          INDIVIDUAL BASIS, NOT AS A PLAINTIFF OR CLASS MEMBER IN ANY CLASS OR
          REPRESENTATIVE ACTION OR PROCEEDING, (2) YOU WILL ONLY BE PERMITTED TO
          SEEK RELIEF (INCLUDING MONETARY, INJUNCTIVE, AND DECLARATORY RELIEF)
          ON AN INDIVIDUAL BASIS, AND (3) YOU MAY NOT BE ABLE TO HAVE ANY CLAIMS
          YOU HAVE AGAINST US RESOLVED BY A JURY OR IN A COURT OF LAW.
        </Paragraph>
        <Paragraph>
          <Bold>Your Privacy</Bold>: At All Hands AI, we respect the privacy of
          our users. For more information please see our Privacy Policy, located
          at <ExternalLink>https://all-hands.dev/privacy</ExternalLink> (the
          “Privacy Policy”). By using the Service, you consent to our
          collection, use and disclosure of personal data and other data as
          outlined therein.
        </Paragraph>
        <Paragraph>
          <Bold>Additional Terms</Bold>: In addition, when using certain
          features through the Service, you will be subject to any additional
          terms applicable to such features that may be posted on or within the
          Service from time to time. All such terms are hereby incorporated by
          reference into these Terms of Service.
        </Paragraph>
      </Section>

      <Section title="Access and Use of the Service">
        <Paragraph>
          <Bold>Service Description</Bold>: The Service is designed to allow
          software developers to efficiently and effectively develop and build
          their own software by using All Hands AI&apos;s proprietary
          open-source software. The Services includes proprietary and third
          party advanced technologies, such as artificial intelligence, machine
          learning systems and similar technology and features (collectively,
          “AI Technology), including third party language models (“LLM”).
        </Paragraph>
        <Paragraph>
          <Bold>Your Registration Obligations</Bold>: You may be required to
          register with All Hands AI or provide information about yourself
          (e.g., name and email address) in order to access and use certain
          features of the Service. If you choose to register for the Service,
          you agree to provide and maintain true, accurate, current, and
          complete information about yourself as prompted by the Service&apos;s
          registration form. Registration data and certain other information
          about you are governed by our Privacy Policy. If you are under 13
          years of age, you are not authorized to use the Service, with or
          without registering. In addition, if you are under 18 years old, you
          may use the Service, with or without registering, only with the
          express consent of your parent or guardian, and you agree to provide
          true, accurate, current, and complete information as requested by All
          Hands AI to confirm such express consent.
        </Paragraph>
        <Paragraph>
          <Bold>Member Account, Password and Security</Bold>: You are
          responsible for maintaining the confidentiality of your password and
          account details, if any, and are fully responsible for any and all
          activities that occur under your password or account. You agree to (a)
          immediately notify All Hands AI of any unauthorized use of your
          password or account or any other breach of security, and (b) ensure
          that you exit from your account at the end of each session when
          accessing the Service. All Hands AI and its current and future
          affiliates (collectively, “All Hands AI Affiliates”) will not be
          liable for any loss or damage arising from your failure to comply with
          this paragraph.
        </Paragraph>
        <Paragraph>
          <Bold>Modifications to Service</Bold>: All Hands AI reserves the right
          to modify or discontinue, temporarily or permanently, the Service (or
          any part thereof) with or without notice. You agree that All Hands AI
          and All Hands AI Affiliates will not be liable to you or to any third
          party for any modification, suspension or discontinuance of the
          Service.
        </Paragraph>
        <Paragraph>
          <Bold>General Practices Regarding Use and Storage</Bold>: You
          acknowledge that All Hands AI may establish general practices and
          limits concerning use of the Service, including the maximum period of
          time that data or other content will be retained by the Service and
          the maximum storage space that will be allotted on All Hands AI&apos;s
          or its third-party service providers&apos; servers on your behalf. You
          agree that All Hands AI has no responsibility or liability for the
          deletion or failure to store any data or other content maintained or
          uploaded by the Service. You acknowledge that All Hands AI reserves
          the right to terminate accounts that are inactive for an extended
          period of time. You further acknowledge that All Hands AI reserves the
          right to change these general practices and limits at any time, in its
          sole discretion, with or without notice.
        </Paragraph>
      </Section>

      <Section title="Conditions of Access and Use">
        <Paragraph>
          <Bold>User Conduct</Bold>: You are solely responsible for all code,
          video, images, information, data, text, software, music, sound,
          photographs, graphics, messages, and other materials (“content”) that
          you make available to All Hands AI, including by uploading, posting,
          publishing, or displaying (hereinafter, “upload(ing)”) via the Service
          or by emailing or otherwise making available to other users of the
          Service (collectively, “User Content”). The following are examples of
          the kinds of content and/or uses that are illegal or prohibited by All
          Hands AI. All Hands AI reserves the right to investigate and take
          appropriate legal action against anyone who, in All Hands AI&apos;s
          sole discretion, violates this provision, including removing the
          offending content from the Service, suspending or terminating the
          account of such violators, and reporting the violator to law
          enforcement authorities. You agree to not use the Service to:
        </Paragraph>
        <OrderedList>
          <li>
            <Paragraph>
              email or otherwise upload any content that (i) infringes any
              intellectual property or other proprietary rights of any party;
              (ii) you do not have a right to upload under any law or under
              contractual or fiduciary relationships; (iii) contains software
              viruses or any other computer code, files or programs designed to
              interrupt, destroy, or limit the functionality of any computer
              software or hardware or telecommunications equipment; (iv) poses
              or creates a privacy or security risk to any person; (v)
              constitutes unsolicited or unauthorized advertising, promotional
              materials, commercial activities and/or sales, “junk mail,”
              “spam,” “chain letters,” “pyramid schemes,” “contests,”
              “sweepstakes,” or any other form of solicitation; (vi) is
              unlawful, harmful, threatening, abusive, harassing, tortious,
              excessively violent, defamatory, vulgar, obscene, pornographic,
              libelous, invasive of another’s privacy, hateful, discriminatory,
              or otherwise objectionable; or (vii) in the sole judgment of All
              Hands AI, is objectionable or which restricts or inhibits any
              other person from using or enjoying the Service, or which may
              expose All Hands AI or its users to any harm or liability of any
              type;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              interfere with or disrupt the Service or servers or networks
              connected to the Service, or disobey any requirements, procedures,
              policies, or regulations of networks connected to the Service;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              violate any applicable local, state, national, or international
              law, or any regulations having the force of law;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              impersonate any person or entity, or falsely state or otherwise
              misrepresent your affiliation with a person or entity;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              solicit personal information from anyone under the age of 18;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              harvest or collect email addresses or other contact information of
              other users from the Service by electronic or other means for the
              purposes of sending unsolicited emails or other unsolicited
              communications;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              advertise or offer to sell or buy any goods or services for any
              business purpose that is not specifically authorized;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              further or promote any criminal activity or enterprise or provide
              instructional information about illegal activities;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              obtain or attempt to access or otherwise obtain any content or
              information through any means not intentionally made available or
              provided for through the Service;
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              circumvent, remove, alter, deactivate, degrade, or thwart any of
              the content protections in or geographic restrictions on any
              content (including Service Content (as defined below)) available
              on or through the Service, including through the use of virtual
              private networks; or
            </Paragraph>
          </li>
          <li>
            <Paragraph>
              engage in or use any data mining, robots, scraping, or similar
              data gathering or extraction methods.
            </Paragraph>
          </li>
        </OrderedList>
        <Paragraph>
          If you are blocked by All Hands AI from accessing the Service
          (including by blocking your IP address), you agree not to implement
          any measures to circumvent such blocking (e.g., by masking your IP
          address or using a proxy IP address or virtual private network).
        </Paragraph>
        <Paragraph>
          <Bold>Competitors</Bold>: No employee, independent contractor, agent,
          or affiliate of any competing open source software development company
          is permitted to view, access, or use any portion of the Service
          without express written permission from All Hands AI. By viewing,
          using, or accessing the Service, you represent and warrant that you
          are not a competitor of All Hands AI or any All Hands AI Affliate, or
          acting on behalf of a competitor of All Hands AI or any All Hands AI
          Affiliate in using or accessing the Service.
        </Paragraph>
        <Paragraph>
          <Bold>Fees</Bold>: To the extent the Service or any portion thereof is
          made available for any fee, you may be required to select a payment
          plan and provide information regarding your credit card or other
          payment instrument. You represent and warrant to All Hands AI that
          such information is true and that you are authorized to use the
          payment instrument. You will promptly update your account information
          with All Hands AI or the Payment Processor (as defined below, as
          applicable, of any changes (for example, a change in your billing
          address or credit card expiration date) that may occur. You agree to
          pay All Hands AI the amount that is specified in the payment plan in
          accordance with the terms of such plan and these Terms of Service. If
          your payment plan includes an ongoing subscription that is
          automatically renewed periodically, you hereby authorize All Hands AI
          through the Payment Processor to bill your payment instrument in
          advance on such periodic basis in accordance with the terms of the
          applicable payment plan until you terminate your account, and you
          further agree to pay any charges so incurred. If you dispute any
          charges you must let All Hands AI know within sixty (60) days after
          the date that All Hands AI charges you, or within such longer period
          of time as may be required under applicable law. We reserve the right
          to change All Hands AI&apos;s prices. If All Hands AI does change
          prices, All Hands AI will provide notice of the change through the
          Service user interface, a pop-up notice, email, or through other
          reasonable means, at All Hands AI&apos;s option, at least thirty (30)
          days before the change is to take effect. Your continued use of the
          Service after the price change becomes effective constitutes your
          agreement to pay the changed amount. You will be responsible for all
          taxes associated with the Service, other than taxes based on All Hands
          AI&apos;s net income.
        </Paragraph>
        <Paragraph>
          <Bold>Payment Processing</Bold>: Notwithstanding any amounts owed to
          Company hereunder, COMPANY DOES NOT PROCESS PAYMENT FOR ANY SERVICES.
          To facilitate payment for the Service via bank account, credit card,
          or debit card, we use third-party payment processors (“Payment
          Processors”). These payment processing services are provided by the
          Payment Processors and are subject to the applicable Payment
          Processor&apos;s terms and conditions, privacy policy, and all other
          relevant agreements (collectively, the “Payment Processor
          Agreements”). By agreeing to these Terms of Service, users that use
          the payment functions of the Service also agree to be bound by the
          applicable Payment Processor Agreement for the payment function the
          user is using, as the same may be modified by the applicable Payment
          Processor from time to time. You hereby authorize the applicable
          Payment Processor to store and continue billing your specified payment
          method even after such payment method has expired, to avoid
          interruptions in payment for your use of the Service. Please contact
          the applicable Payment Processor for more information. Company assumes
          no liability or responsibility for any payments you make through the
          Service.
        </Paragraph>
        <Paragraph>
          <Bold>Refunds and Cancellations</Bold>: Payments made by you hereunder
          are final and non-refundable, unless otherwise determined by Company.
          You may cancel your subscription online by emailing us at:{" "}
          <Mailto>contact@all-hands.dev</Mailto>
        </Paragraph>
        <Paragraph>
          <Bold>Commercial Use</Bold>: Unless otherwise expressly authorized
          herein or in the Service, you agree not to display, distribute,
          license, perform, publish, reproduce, duplicate, copy, create
          derivative works from, modify, sell, resell, grant access to,
          transfer, or otherwise use or exploit any portion of the Service for
          any commercial purposes. The Service is for your personal use.
        </Paragraph>
      </Section>

      <Section title="Mobile Services and Software">
        <Paragraph>
          Mobile Services: The Service includes certain services that are
          available via a mobile device, including (i) the ability to upload
          content to the Service via a mobile device, (ii) the ability to browse
          the Service and the Site from a mobile device, and (iii) the ability
          to access certain features and content through Mobile Apps
          (collectively, the “Mobile Services”). To the extent you access the
          Service through a mobile device, your wireless service carrier&apos;s
          standard charges, data rates, and other fees may apply. In addition,
          downloading, installing, or using certain Mobile Services may be
          prohibited or restricted by your carrier, and not all Mobile Services
          may work with all carriers or devices.
        </Paragraph>
        <Paragraph>
          <Bold>Ownership; Restrictions</Bold>: The technology and software
          underlying the Service or distributed in connection therewith are the
          property of All Hands AI, All Hands AI Affiliates, and their licensors
          ( the “Software”). You agree not to copy, modify, create a derivative
          work of, reverse engineer, reverse assemble, or otherwise attempt to
          discover any source code, sell, assign, sublicense, or otherwise
          transfer any right in the Software. Any rights not expressly granted
          herein are reserved by All Hands AI.
        </Paragraph>
        <Paragraph>
          <Bold>Special Notice for International Use; Export Controls</Bold>:
          All Hands AI is headquartered in the United States. Whether inside or
          outside of the United States, you are solely responsible for ensuring
          compliance with the laws of your specific jurisdiction. Software
          available in connection with the Service and the transmission of
          applicable data, if any, is subject to United States export controls.
          No Software may be downloaded from the Service or otherwise exported
          or re-exported in violation of U.S. export laws. Downloading,
          accessing or using the Software or Services is at your sole risk.
        </Paragraph>
        <Paragraph>
          <Bold>Open Source Software</Bold>: The Software may contain or be
          provided together with open source software. Each item of open source
          software is subject to its own license terms, which can be found at{" "}
          <ExternalLink>https://github.com/opendevin/opendevin</ExternalLink>.
          If required by any license for particular open source software, All
          Hands AI makes such open source software, and All Hands AI&apos;s
          modifications to that open source software (if any), available by
          written request to <Mailto>contact@all-hands.dev</Mailto>. Copyrights
          to the open source software are held by the respective copyright
          holders indicated therein.
        </Paragraph>
      </Section>

      <Section title="Intellectual Property Rights">
        <Paragraph>
          <Bold>Service Content</Bold>: You acknowledge and agree that the
          Service may contain content or features (“Service Content”) that are
          protected by copyright, patent, trademark, trade secret, or other
          proprietary rights and laws. Except as expressly authorized by All
          Hands AI, you agree not to modify, copy, frame, scrape, rent, lease,
          loan, sell, distribute, or create derivative works based on the
          Service or the Service Content, in whole or in part, except that the
          foregoing does not apply to your own User Content (as defined below)
          that you upload to or make available through the Service in accordance
          with these Terms of Service. Any use of the Service or the Service
          Content other than as specifically authorized herein is strictly
          prohibited.
        </Paragraph>
        <Paragraph>
          <Bold>Trademarks</Bold>: The All Hands AI name and logos are
          trademarks and service marks of All Hands AI (collectively the “All
          Hands AI Trademarks”). Other company, product, and service names and
          logos used and displayed via the Service may be trademarks or service
          marks of their respective owners who may or may not endorse or be
          affiliated with or connected to All Hands AI. Nothing in these Terms
          of Service or the Service should be construed as granting, by
          implication, estoppel, or otherwise, any license or right to use any
          of All Hands AI Trademarks displayed on the Service, without our prior
          written permission in each instance. All goodwill generated from the
          use of All Hands AI Trademarks will inure to our exclusive benefit.
        </Paragraph>
        <Paragraph>
          <Bold>Third-Party Material</Bold>: Under no circumstances will All
          Hands AI or any All Hands AI Affiliate be liable in any way for any
          content or materials of any third parties (including users), including
          for any errors or omissions in any content, or for any loss or damage
          of any kind incurred as a result of the use of any such content. You
          acknowledge that All Hands AI does not pre-screen content, but that
          All Hands AI and its designees will have the right (but not the
          obligation) in their sole discretion to refuse or remove any content
          that is available via the Service. Without limiting the foregoing, All
          Hands AI and its designees will have the right to remove any content
          that violates these Terms of Service or is deemed by All Hands AI, in
          its sole discretion, to be otherwise objectionable. You agree that you
          must evaluate, and bear all risks associated with, the use of any
          content, including any reliance on the accuracy, completeness, or
          usefulness of such content.
        </Paragraph>
        <Paragraph>
          <Bold>User Content</Bold>: You represent and warrant that you own all
          right, title and interest in and to such User Content, including all
          copyrights and rights of publicity contained therein. You hereby grant
          All Hands AI and All Hands AI Affiliates, and their successors and
          assigns, a non-exclusive, worldwide, royalty-free, fully paid-up,
          transferable, sublicensable (directly and indirectly through multiple
          tiers), perpetual, and irrevocable license to copy, display, upload,
          perform, distribute, store, modify, and otherwise use your User
          Content (including any name, username, voice, image or likeness
          incorporated therein or otherwise provided by you), in any form,
          medium or technology now known or later developed, (a) in connection
          with the operation of the Service, (b) to provide, develop and improve
          the Service and other offerings of All Hands AI and/or All Hands AI
          Affiliates, including in connection with training models and
          algorithms, (c) for the promotion, advertising or marketing of the
          foregoing; and (d) as otherwise set forth in our Privacy Policy. This
          license includes the right for All Hands AI and All Hands AI
          Affiliates to make your User Content available for syndication,
          broadcast, distribution or publication by other companies,
          organizations or individuals that partner with All Hands AI or a All
          Hands AI Affiliate. You also agree that All Hands AI may remove
          metadata associated with your User Content, and you irrevocably waive
          any claims and assertions of moral rights or attribution with respect
          to your User Content. You assume all risk associated with your User
          Content and the transmission of your User Content, and you have sole
          responsibility for the accuracy, quality, legality and appropriateness
          of your User Content.
        </Paragraph>
        <Paragraph>
          You hereby authorize All Hands AI and All Hands AI Affiliates and
          their third-party service providers to collect and analyze User
          Content and other data and information relating to the Service and
          related systems and technologies and derive statistical and usage data
          relating thereto (collectively, “Usage Data”). All Hands AI and All
          Hands AI Affiliates may use Usage Data for any purpose in accordance
          with applicable law and our Privacy Policy.
        </Paragraph>
        <Paragraph>
          Any questions, comments, suggestions, ideas, feedback, reviews, or
          other information about the Service (“Submissions”), provided by you
          to All Hands AI or any All Hands AI Affiliate are non-confidential and
          All Hands AI and All Hands AI Affiliates will be entitled to the
          unrestricted use and dissemination of these Submissions for any
          purpose, commercial or otherwise, without acknowledgment, attribution,
          or compensation to you.
        </Paragraph>
        <Paragraph>
          You acknowledge and agree that All Hands AI may preserve User Content
          and may also disclose User Content if required to do so by law or in
          the good faith belief that such preservation or disclosure is
          reasonably necessary to: (a) comply with legal process, applicable
          laws, or government requests; (b) enforce these Terms of Service; (c)
          respond to claims that any content violates the rights of third
          parties; or (d) protect the rights, property, or personal safety of
          All Hands AI, its users, or the public. You understand that the
          technical processing and transmission of the Service, including your
          User Content, may involve (i) transmissions over various networks; and
          (ii) changes to conform and adapt to technical requirements of
          connecting networks or devices.
        </Paragraph>
      </Section>

      <Section title="Third-Party Services and Websites">
        <Paragraph>
          The Service may provide links or other access to services, sites,
          technology, and resources that are provided or otherwise made
          available by third parties (the “Third-Party Services”). Additionally,
          you may enable or log in to the Service via various online Third-Party
          Services, such as GitHub. Your access and use of the Third-Party
          Services may also be subject to additional terms and conditions,
          privacy policies, or other agreements with such third party, and you
          may be required to authenticate to or create separate accounts to use
          Third-Party Services on the websites or via the technology platforms
          of their respective providers. Some Third-Party Services will provide
          us with access to certain information that you have provided to third
          parties, including through such Third-Party Services, and we will use,
          store and disclose such information in accordance with our Privacy
          Policy. For more information about the implications of activating
          Third-Party Services and our use, storage and disclosure of
          information related to you and your use of such Third-Party Services
          within the Service, please see our Privacy Policy. All Hands AI has no
          control over and is not responsible for such Third-Party Services,
          including for the accuracy, availability, reliability, or completeness
          of information shared by or available through Third-Party Services, or
          on the privacy practices of Third-Party Services. We encourage you to
          review the privacy policies of the third parties providing Third-Party
          Services prior to using such services. You, and not All Hands AI or
          any All Hands AI Affiliate, will be responsible for any and all costs
          and charges associated with your use of any Third-Party Services. All
          Hands AI enables these Third-Party Services merely as a convenience
          and the integration or inclusion of such Third-Party Services does not
          imply an endorsement or recommendation. Any dealings you have with
          third parties while using the Service are between you and the third
          party. All Hands AI and All Hands AI Affiliates will not be
          responsible or liable, directly or indirectly, for any damage or loss
          caused or alleged to be caused by or in connection with use of or
          reliance on any Third-Party Services.
        </Paragraph>
      </Section>

      <Section title="Indemnification">
        <Paragraph>
          To the extent permitted under applicable law, you agree to defend,
          indemnify, and hold harmless All Hands AI and All Hands AI Affiliates,
          and its and their respective officers, employees, directors, service
          providers, licensors, and agents (collectively, the “All Hands AI
          Parties”), from any and all losses, damages, expenses, including
          reasonable attorneys&apos; fees, rights, claims, actions of any kind,
          and injury (including death) arising out of or relating to your use of
          the Service, any User Content, your connection to the Service, your
          violation of these Terms of Service, or your violation of any rights
          of another. All Hands AI will provide notice to you of any such claim,
          suit, or proceeding. All Hands AI reserves the right to assume the
          exclusive defense and control of any matter which is subject to
          indemnification under this section, and you agree to cooperate with
          any reasonable requests assisting All Hands AI&apos;s defense of such
          matter. You may not settle or compromise any claim against the All
          Hands AI Parties without All Hands AI&apos;s written consent.
        </Paragraph>
      </Section>

      <Section title="AI Technology">
        <Paragraph>
          AI Technology is new and evolving. Some AI Technology, including third
          party LLM made available through the Services, allow users to submit
          queries or other prompts, and the AI Technology will generate and
          return to you content, recommendations, data, or other information
          through the Services (“Output”).
        </Paragraph>
        <Paragraph>
          You acknowledge and agree that, in addition to the limitations and
          restrictions set forth in this Agreement, there are numerous
          limitations that apply with respect to AI Technology and the Output it
          generates, including that (i) it may contain errors or misleading
          information and may not be accurate or reliable; (ii) AI Technology is
          based on predefined rules and algorithms that lack the ability to
          think creatively and come up with new ideas and can result in
          repetitive or formulaic content; (iii) AI Technology can struggle with
          understanding the nuances of language, including slang, idioms, and
          cultural references, which can result in Output that is out of context
          or does not make sense; (iv) AI Technology does not have emotions and
          cannot understand or convey emotions in the way humans can, which can
          result in Output that lacks the empathy and emotion that humans are
          able to convey; (v) AI Technology can perpetuate biases that are
          present in the data used to train them, which can result in Output
          that is discriminatory or offensive; (vi) AI Technology can struggle
          with complex tasks that require reasoning, judgment and
          decision-making; (vii) AI Technology require large amounts of data to
          train and generate content, and the data used to train AI Technology
          may be of poor quality or biased, which will negatively impact the
          accuracy and quality of the generated Output; and (viii) AI
          Technology-generated Output can lack the personal touch that comes
          with content created by humans, which can make it seem cold and
          impersonal.
        </Paragraph>
        <Paragraph>
          You will use independent judgement and discretion before relying on or
          otherwise using Output. Output is for informational purposes only and
          is not a substitute for advice from a qualified professional. You will
          use discretion before instructing AI Technology to take any actions on
          your behalf, and are solely responsible for monitoring and approving
          any such actions.
        </Paragraph>
        <Paragraph>
          All Hands AI bears no liability to you or anyone else arising from or
          relating to your use of AI Technology.
        </Paragraph>
      </Section>

      <Section title="Disclaimer of Warranties">
        <Paragraph>
          YOUR USE OF THE SERVICE IS AT YOUR SOLE RISK. THE SERVICE IS PROVIDED
          ON AN “AS IS” AND “AS AVAILABLE” BASIS. THE ALL HANDS AI PARTIES
          EXPRESSLY DISCLAIM ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS,
          IMPLIED OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF
          MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND
          NON-INFRINGEMENT.
        </Paragraph>
        <Paragraph>
          THE ALL HANDS AI PARTIES MAKE NO WARRANTY THAT (A) THE SERVICE WILL
          MEET YOUR REQUIREMENTS; (B) THE SERVICE WILL BE UNINTERRUPTED, TIMELY,
          SECURE, OR ERROR-FREE; (C) THE RESULTS THAT MAY BE OBTAINED FROM THE
          USE OF THE SERVICE WILL BE ACCURATE OR RELIABLE; OR (D) THE QUALITY OF
          ANY PRODUCTS, SERVICES, INFORMATION, OR OTHER MATERIAL PURCHASED OR
          OBTAINED BY YOU THROUGH THE SERVICE WILL MEET YOUR EXPECTATIONS.
        </Paragraph>
      </Section>

      <Section title="Limitation of Liability">
        <Paragraph>
          YOU EXPRESSLY UNDERSTAND AND AGREE THAT THE ALL HANDS AI PARTIES WILL
          NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL,
          EXEMPLARY DAMAGES, OR DAMAGES FOR LOSS OF PROFITS INCLUDING DAMAGES
          FOR LOSS OF GOODWILL, USE, OR DATA OR OTHER INTANGIBLE LOSSES (EVEN IF
          THE ALL HANDS AI PARTIES HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH
          DAMAGES), WHETHER BASED ON CONTRACT, TORT, NEGLIGENCE, STRICT
          LIABILITY, OR OTHERWISE, RESULTING FROM: (A) THE USE OR THE INABILITY
          TO USE THE SERVICE; (B) THE COST OF PROCUREMENT OF SUBSTITUTE GOODS
          AND SERVICES RESULTING FROM ANY GOODS, DATA, INFORMATION, OR SERVICES
          PURCHASED OR OBTAINED OR MESSAGES RECEIVED OR TRANSACTIONS ENTERED
          INTO THROUGH OR FROM THE SERVICE; (C) UNAUTHORIZED ACCESS TO OR
          ALTERATION OF YOUR TRANSMISSIONS OR DATA; (D) STATEMENTS OR CONDUCT OF
          ANY THIRD PARTY ON THE SERVICE; OR (E) ANY OTHER MATTER RELATING TO
          THE SERVICE. IN NO EVENT WILL THE ALL HANDS AI PARTIES&apos; TOTAL
          LIABILITY TO YOU FOR ALL DAMAGES, LOSSES, OR CAUSES OF ACTION EXCEED
          ONE HUNDRED DOLLARS ($100).
        </Paragraph>
        <Paragraph>
          SOME JURISDICTIONS DO NOT ALLOW THE DISCLAIMER OR EXCLUSION OF CERTAIN
          WARRANTIES OR THE LIMITATION OR EXCLUSION OF LIABILITY FOR INCIDENTAL
          OR CONSEQUENTIAL DAMAGES. ACCORDINGLY, SOME OF THE ABOVE LIMITATIONS
          SET FORTH ABOVE MAY NOT APPLY TO YOU OR BE ENFORCEABLE WITH RESPECT TO
          YOU. IF YOU ARE DISSATISFIED WITH ANY PORTION OF THE SERVICE OR WITH
          THESE TERMS OF SERVICE, YOUR SOLE AND EXCLUSIVE REMEDY IS TO
          DISCONTINUE USE OF THE SERVICE.
        </Paragraph>
        <Paragraph>
          IF YOU ARE A USER FROM NEW JERSEY, THE FOREGOING SECTIONS TITLED
          “INDEMNIFICATION”, “DISCLAIMER OF WARRANTIES” AND “LIMITATION OF
          LIABILITY” ARE INTENDED TO BE ONLY AS BROAD AS IS PERMITTED UNDER THE
          LAWS OF THE STATE OF NEW JERSEY. IF ANY PORTION OF THESE SECTIONS IS
          HELD TO BE INVALID UNDER THE LAWS OF THE STATE OF NEW JERSEY, THE
          INVALIDITY OF SUCH PORTION WILL NOT AFFECT THE VALIDITY OF THE
          REMAINING PORTIONS OF THE APPLICABLE SECTIONS.
        </Paragraph>
      </Section>

      <Section title="Dispute Resolution By Binding Arbitration">
        <Paragraph bold>
          PLEASE READ THIS SECTION CAREFULLY AS IT AFFECTS YOUR RIGHTS.
        </Paragraph>
        <OrderedList>
          <li>
            <Bold>Agreement to Arbitrate</Bold>
            <Paragraph>
              This Dispute Resolution by Binding Arbitration section is referred
              to in these Terms of Service as the “Arbitration Agreement.” You
              agree that any and all disputes or claims that have arisen or may
              arise between you and All Hands AI, whether arising out of or
              relating to these Terms of Service (including any alleged breach
              thereof), the Service, any advertising, or any aspect of the
              relationship or transactions between us, will be resolved
              exclusively through final and binding arbitration, rather than a
              court, in accordance with the terms of this Arbitration Agreement,
              except that you may assert individual claims in small claims
              court, if your claims qualify. Further, this Arbitration Agreement
              does not preclude you from bringing issues to the attention of
              federal, state, or local agencies, and such agencies can, if the
              law allows, seek relief against us on your behalf. You agree that,
              by entering into these Terms of Service, you and All Hands AI are
              each waiving the right to a trial by jury or to participate in a
              class action. Your rights will be determined by a neutral
              arbitrator, not a judge or jury. The Federal Arbitration Act
              governs the interpretation and enforcement of this Arbitration
              Agreement.
            </Paragraph>
          </li>
          <li>
            <Bold>
              Prohibition of Class and Representative Actions and
              Non-Individualized Relief
            </Bold>
            <Paragraph bold italic>
              YOU AND ALL HANDS AI AGREE THAT EACH OF US MAY BRING CLAIMS
              AGAINST THE OTHER ONLY ON AN INDIVIDUAL BASIS AND NOT AS A
              PLAINTIFF OR CLASS MEMBER IN ANY PURPORTED CLASS OR REPRESENTATIVE
              ACTION OR PROCEEDING. UNLESS BOTH YOU AND ALL HANDS AI AGREE
              OTHERWISE, THE ARBITRATOR MAY NOT CONSOLIDATE OR JOIN MORE THAN
              ONE PERSON&apos;S OR PARTY&apos;S CLAIMS AND MAY NOT OTHERWISE
              PRESIDE OVER ANY FORM OF A CONSOLIDATED, REPRESENTATIVE, OR CLASS
              PROCEEDING. ALSO, THE ARBITRATOR MAY AWARD RELIEF (INCLUDING
              MONETARY, INJUNCTIVE, AND DECLARATORY RELIEF) ONLY IN FAVOR OF THE
              INDIVIDUAL PARTY SEEKING RELIEF AND ONLY TO THE EXTENT NECESSARY
              TO PROVIDE RELIEF NECESSITATED BY THAT PARTY&apos;S INDIVIDUAL
              CLAIM(S), EXCEPT THAT YOU MAY PURSUE A CLAIM FOR AND THE
              ARBITRATOR MAY AWARD PUBLIC INJUNCTIVE RELIEF UNDER APPLICABLE LAW
              TO THE EXTENT REQUIRED FOR THE ENFORCEABILITY OF THIS PROVISION.
            </Paragraph>
          </li>
          <li>
            <Bold>Pre-Arbitration Dispute Resolution</Bold>
            <Paragraph>
              All Hands AI is always interested in resolving disputes amicably
              and efficiently, and most customer concerns can be resolved
              quickly and to the customer&apos;s satisfaction by emailing
              customer support at <Mailto>contact@all-hands.dev</Mailto>. If
              such efforts prove unsuccessful, a party who intends to seek
              arbitration must first send to the other, by certified mail, a
              written Notice of Dispute (“Notice”). The Notice to All Hands AI
              should be sent to 12 Cady Avenue, Somerville, MA 02144 (“Notice
              Address”). The Notice must (i) describe the nature and basis of
              the claim or dispute and (ii) set forth the specific relief
              sought. If All Hands AI and you do not resolve the claim within
              sixty (60) calendar days after the Notice is received, you or All
              Hands AI may commence an arbitration proceeding. During the
              arbitration, the amount of any settlement offer made by All Hands
              AI or you will not be disclosed to the arbitrator until after the
              arbitrator determines the amount, if any, to which you or All
              Hands AI is entitled.
            </Paragraph>
          </li>
          <li>
            <Bold>Arbitration Procedures</Bold>
            <Paragraph>
              Arbitration will be conducted by a neutral arbitrator in
              accordance with the American Arbitration Association&apos;s
              (“AAA”) rules and procedures, including the AAA&apos;s Consumer
              Arbitration Rules (collectively, the “AAA Rules”), as modified by
              this Arbitration Agreement. For information on the AAA, please
              visit its website, https://www.adr.org. Information about the AAA
              Rules and fees for consumer disputes can be found at the
              AAA&apos;s consumer arbitration page,
              https://www.adr.org/consumer. If there is any inconsistency
              between any term of the AAA Rules and any term of this Arbitration
              Agreement, the applicable terms of this Arbitration Agreement will
              control unless the arbitrator determines that the application of
              the inconsistent Arbitration Agreement terms would not result in a
              fundamentally fair arbitration. The arbitrator must also follow
              the provisions of these Terms of Service as a court would. All
              issues are for the arbitrator to decide, including issues relating
              to the scope, enforceability, and arbitrability of this
              Arbitration Agreement. Although arbitration proceedings are
              usually simpler and more streamlined than trials and other
              judicial proceedings, the arbitrator can award the same damages
              and relief on an individual basis that a court can award to an
              individual under these Terms of Service and applicable law.
              Decisions by the arbitrator are enforceable in court and may be
              overturned by a court only for very limited reasons.
            </Paragraph>
            <Paragraph>
              Unless All Hands AI and you agree otherwise, any arbitration
              hearings will take place in a reasonably convenient location for
              both parties with due consideration of their ability to travel and
              other pertinent circumstances. If the parties are unable to agree
              on a location, the determination will be made by AAA. If your
              claim is for $10,000 or less, All Hands AI agrees that you may
              choose whether the arbitration will be conducted solely on the
              basis of documents submitted to the arbitrator, through a
              telephonic hearing, or by an in-person hearing as established by
              the AAA Rules. If your claim exceeds $10,000, the right to a
              hearing will be determined by the AAA Rules. Regardless of the
              manner in which the arbitration is conducted, the arbitrator will
              issue a reasoned written decision sufficient to explain the
              essential findings and conclusions on which the award is based.
            </Paragraph>
          </li>
          <li>
            <Bold>Costs of Arbitration</Bold>
            <Paragraph>
              Payment of all filing, administration, and arbitrator fees
              (collectively, the “Arbitration Fees”) will be governed by the AAA
              Rules, unless otherwise provided in this Arbitration Agreement. To
              the extent any Arbitration Fees are not specifically allocated to
              either All Hands AI or you under the AAA Rules, All Hands AI and
              you shall split them equally; provided that if you are able to
              demonstrate to the arbitrator that you are economically unable to
              pay your portion of such Arbitration Fees or if the arbitrator
              otherwise determines for any reason that you should not be
              required to pay your portion of any Arbitration Fees, All Hands AI
              will pay your portion of such fees. In addition, if you
              demonstrate to the arbitrator that the costs of arbitration will
              be prohibitive as compared to the costs of litigation, All Hands
              AI will pay as much of the Arbitration Fees as the arbitrator
              deems necessary to prevent the arbitration from being
              cost-prohibitive. Any payment of attorneys&apos; fees will be
              governed by the AAA Rules.
            </Paragraph>
          </li>
          <li>
            <Bold>Confidentiality</Bold>
            <Paragraph>
              All aspects of the arbitration proceeding, and any ruling,
              decision, or award by the arbitrator, will be strictly
              confidential for the benefit of all parties.
            </Paragraph>
          </li>
          <li>
            <Bold>Severability</Bold>
            <Paragraph>
              If a court or the arbitrator decides that any term or provision of
              this Arbitration Agreement (other than the subsection (b) above
              titled “Prohibition of Class and Representative Actions and
              Non-Individualized Relief” above) is invalid or unenforceable, the
              parties agree to replace such term or provision with a term or
              provision that is valid and enforceable and that comes closest to
              expressing the intention of the invalid or unenforceable term or
              provision, and this Arbitration Agreement will be enforceable as
              so modified. If a court or the arbitrator decides that any of the
              provisions of subsection (b) above titled “Prohibition of Class
              and Representative Actions and Non-Individualized Relief” are
              invalid or unenforceable, then the entirety of this Arbitration
              Agreement will be null and void, unless such provisions are deemed
              to be invalid or unenforceable solely with respect to claims for
              public injunctive relief. The remainder of these Terms of Service
              will continue to apply.
            </Paragraph>
          </li>
          <li>
            <Bold>Future Changes to Arbitration Agreement</Bold>
            <Paragraph>
              Notwithstanding any provision in these Terms of Service to the
              contrary, All Hands AI agrees that if it makes any future change
              to this Arbitration Agreement (other than a change to the Notice
              Address) while you are a user of the Service, you may reject any
              such change by sending All Hands AI written notice within thirty
              (30) calendar days of the change to the Notice Address provided
              above. By rejecting any future change, you are agreeing that you
              will arbitrate any dispute between us in accordance with the
              language of this Arbitration Agreement as of the date you first
              accepted these Terms of Service (or accepted any subsequent
              changes to these Terms of Service).
            </Paragraph>
          </li>
        </OrderedList>
      </Section>

      <Section title="Termination">
        <Paragraph>
          You agree that All Hands AI, in its sole discretion, may suspend or
          terminate your account (or any part thereof) or use of the Service and
          remove and discard any content within the Service, for any reason,
          including for lack of use or if All Hands AI believes that you have
          violated or acted inconsistently with the letter or spirit of these
          Terms of Service. Any suspected fraudulent, abusive, or illegal
          activity that may be grounds for termination of your use of the
          Service, may be referred to appropriate law enforcement authorities.
          All Hands AI may also in its sole discretion and at any time
          discontinue providing the Service, or any part thereof, with or
          without notice. You agree that any termination of your access to the
          Service under any provision of these Terms of Service may be effected
          without prior notice, and acknowledge and agree that All Hands AI may
          immediately deactivate or delete your account and all related
          information and files in your account and/or bar any further access to
          such files or the Service. Further, you agree that All Hands AI and
          All Hands AI Affiliates will not be liable to you or any third party
          for any termination of your access to the Service.
        </Paragraph>
      </Section>

      <Section title="User Disputes">
        <Paragraph>
          You agree that you are solely responsible for your interactions with
          any other user in connection with the Service, and All Hands AI and
          All Hands AI Affiliates will have no liability or responsibility with
          respect thereto. All Hands AI reserves the right, but has no
          obligation, to become involved in any way with disputes between you
          and any other user of the Service.
        </Paragraph>
      </Section>

      <Section title="General">
        <Paragraph>
          These Terms of Service (together with the terms incorporated by
          reference herein) constitute the entire agreement between you and All
          Hands AI governing your access and use of the Service, and supersede
          any prior agreements between you and All Hands AI with respect to the
          Service. You also may be subject to additional terms and conditions
          that may apply when you use Third-Party Services, third-party content
          or third-party software. These Terms of Service will be governed by
          the laws of the State of Delaware without regard to its conflict of
          law provisions. With respect to any disputes or claims not subject to
          arbitration, as set forth above, you and All Hands AI submit to the
          personal and exclusive jurisdiction of the state and federal courts
          located within the State of Delaware. The failure of All Hands AI to
          exercise or enforce any right or provision of these Terms of Service
          will not constitute a waiver of such right or provision. If any
          provision of these Terms of Service is found by a court of competent
          jurisdiction to be invalid, the parties nevertheless agree that the
          court should endeavor to give effect to the parties&apos; intentions
          as reflected in the provision, and the other provisions of these Terms
          of Service remain in full force and effect. You agree that regardless
          of any statute or law to the contrary, any claim or cause of action
          arising out of or related to use of the Service or these Terms of
          Service must be filed within one (1) year after such claim or cause of
          action arose or be forever barred. A printed version of these Terms of
          Service and of any notice given in electronic form will be admissible
          in judicial or administrative proceedings based upon or relating to
          these Terms of Service to the same extent and subject to the same
          conditions as other business documents and records originally
          generated and maintained in printed form. You may not assign these
          Terms of Service without the prior written consent of All Hands AI,
          but All Hands AI may assign or transfer these Terms of Service, in
          whole or in part, without restriction. The section titles in these
          Terms of Service are for convenience only and have no legal or
          contractual effect. As used in these Terms of Service, the words
          “include” and “including,” and variations thereof, will not be deemed
          to be terms of limitation, but rather will be deemed to be followed by
          the words “without limitation.” Notices to you may be made via either
          email or regular mail. The Service may also provide notices to you of
          changes to these Terms of Service or other matters by displaying
          notices or links to notices generally on the Service. All Hands AI
          will not be in default hereunder by reason of any failure or delay in
          the performance of its obligations where such failure or delay is due
          to civil disturbances, riot, epidemic, hostilities, war, terrorist
          attack, embargo, natural disaster, acts of God, flood, fire, sabotage,
          fluctuations or unavailability of electrical power, network access or
          equipment, or any other circumstances or causes beyond All Hands
          AI&apos;s reasonable control.
        </Paragraph>
      </Section>

      <Section title="U.S. Government Restricted Rights">
        <Paragraph>
          The Service is made available to the U.S. government with “RESTRICTED
          RIGHTS.” Use, duplication, or disclosure by the U.S. government is
          subject to the restrictions contained in 48 CFR 52.227-19 and 48 CFR
          252.227-7013 et seq. or its successor. Access or use of the Service
          (including the Software) by the U.S. government constitutes
          acknowledgement of our proprietary rights in the Service (including
          the Software).
        </Paragraph>
      </Section>

      <Section title="Questions? Concerns? Suggestions?">
        <Paragraph>
          Please contact us at <Mailto>contact@all-hands.dev</Mailto> to report
          any violations of these Terms of Service or to pose any questions
          regarding these Terms of Service or the Service.
        </Paragraph>
      </Section>
    </main>
  );
}

export default TOS;
