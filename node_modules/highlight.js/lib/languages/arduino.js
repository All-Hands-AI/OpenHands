/**
 * @param {string} value
 * @returns {RegExp}
 * */

/**
 * @param {RegExp | string } re
 * @returns {string}
 */
function source(re) {
  if (!re) return null;
  if (typeof re === "string") return re;

  return re.source;
}

/**
 * @param {RegExp | string } re
 * @returns {string}
 */
function lookahead(re) {
  return concat('(?=', re, ')');
}

/**
 * @param {RegExp | string } re
 * @returns {string}
 */
function optional(re) {
  return concat('(', re, ')?');
}

/**
 * @param {...(RegExp | string) } args
 * @returns {string}
 */
function concat(...args) {
  const joined = args.map((x) => source(x)).join("");
  return joined;
}

/*
Language: C++
Category: common, system
Website: https://isocpp.org
*/

/** @type LanguageFn */
function cPlusPlus(hljs) {
  // added for historic reasons because `hljs.C_LINE_COMMENT_MODE` does
  // not include such support nor can we be sure all the grammars depending
  // on it would desire this behavior
  const C_LINE_COMMENT_MODE = hljs.COMMENT('//', '$', {
    contains: [
      {
        begin: /\\\n/
      }
    ]
  });
  const DECLTYPE_AUTO_RE = 'decltype\\(auto\\)';
  const NAMESPACE_RE = '[a-zA-Z_]\\w*::';
  const TEMPLATE_ARGUMENT_RE = '<[^<>]+>';
  const FUNCTION_TYPE_RE = '(' +
    DECLTYPE_AUTO_RE + '|' +
    optional(NAMESPACE_RE) +
    '[a-zA-Z_]\\w*' + optional(TEMPLATE_ARGUMENT_RE) +
  ')';
  const CPP_PRIMITIVE_TYPES = {
    className: 'keyword',
    begin: '\\b[a-z\\d_]*_t\\b'
  };

  // https://en.cppreference.com/w/cpp/language/escape
  // \\ \x \xFF \u2837 \u00323747 \374
  const CHARACTER_ESCAPES = '\\\\(x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4,8}|[0-7]{3}|\\S)';
  const STRINGS = {
    className: 'string',
    variants: [
      {
        begin: '(u8?|U|L)?"',
        end: '"',
        illegal: '\\n',
        contains: [ hljs.BACKSLASH_ESCAPE ]
      },
      {
        begin: '(u8?|U|L)?\'(' + CHARACTER_ESCAPES + "|.)",
        end: '\'',
        illegal: '.'
      },
      hljs.END_SAME_AS_BEGIN({
        begin: /(?:u8?|U|L)?R"([^()\\ ]{0,16})\(/,
        end: /\)([^()\\ ]{0,16})"/
      })
    ]
  };

  const NUMBERS = {
    className: 'number',
    variants: [
      {
        begin: '\\b(0b[01\']+)'
      },
      {
        begin: '(-?)\\b([\\d\']+(\\.[\\d\']*)?|\\.[\\d\']+)((ll|LL|l|L)(u|U)?|(u|U)(ll|LL|l|L)?|f|F|b|B)'
      },
      {
        begin: '(-?)(\\b0[xX][a-fA-F0-9\']+|(\\b[\\d\']+(\\.[\\d\']*)?|\\.[\\d\']+)([eE][-+]?[\\d\']+)?)'
      }
    ],
    relevance: 0
  };

  const PREPROCESSOR = {
    className: 'meta',
    begin: /#\s*[a-z]+\b/,
    end: /$/,
    keywords: {
      'meta-keyword':
        'if else elif endif define undef warning error line ' +
        'pragma _Pragma ifdef ifndef include'
    },
    contains: [
      {
        begin: /\\\n/,
        relevance: 0
      },
      hljs.inherit(STRINGS, {
        className: 'meta-string'
      }),
      {
        className: 'meta-string',
        begin: /<.*?>/
      },
      C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE
    ]
  };

  const TITLE_MODE = {
    className: 'title',
    begin: optional(NAMESPACE_RE) + hljs.IDENT_RE,
    relevance: 0
  };

  const FUNCTION_TITLE = optional(NAMESPACE_RE) + hljs.IDENT_RE + '\\s*\\(';

  const COMMON_CPP_HINTS = [
    'asin',
    'atan2',
    'atan',
    'calloc',
    'ceil',
    'cosh',
    'cos',
    'exit',
    'exp',
    'fabs',
    'floor',
    'fmod',
    'fprintf',
    'fputs',
    'free',
    'frexp',
    'auto_ptr',
    'deque',
    'list',
    'queue',
    'stack',
    'vector',
    'map',
    'set',
    'pair',
    'bitset',
    'multiset',
    'multimap',
    'unordered_set',
    'fscanf',
    'future',
    'isalnum',
    'isalpha',
    'iscntrl',
    'isdigit',
    'isgraph',
    'islower',
    'isprint',
    'ispunct',
    'isspace',
    'isupper',
    'isxdigit',
    'tolower',
    'toupper',
    'labs',
    'ldexp',
    'log10',
    'log',
    'malloc',
    'realloc',
    'memchr',
    'memcmp',
    'memcpy',
    'memset',
    'modf',
    'pow',
    'printf',
    'putchar',
    'puts',
    'scanf',
    'sinh',
    'sin',
    'snprintf',
    'sprintf',
    'sqrt',
    'sscanf',
    'strcat',
    'strchr',
    'strcmp',
    'strcpy',
    'strcspn',
    'strlen',
    'strncat',
    'strncmp',
    'strncpy',
    'strpbrk',
    'strrchr',
    'strspn',
    'strstr',
    'tanh',
    'tan',
    'unordered_map',
    'unordered_multiset',
    'unordered_multimap',
    'priority_queue',
    'make_pair',
    'array',
    'shared_ptr',
    'abort',
    'terminate',
    'abs',
    'acos',
    'vfprintf',
    'vprintf',
    'vsprintf',
    'endl',
    'initializer_list',
    'unique_ptr',
    'complex',
    'imaginary',
    'std',
    'string',
    'wstring',
    'cin',
    'cout',
    'cerr',
    'clog',
    'stdin',
    'stdout',
    'stderr',
    'stringstream',
    'istringstream',
    'ostringstream'
  ];

  const CPP_KEYWORDS = {
    keyword: 'int float while private char char8_t char16_t char32_t catch import module export virtual operator sizeof ' +
      'dynamic_cast|10 typedef const_cast|10 const for static_cast|10 union namespace ' +
      'unsigned long volatile static protected bool template mutable if public friend ' +
      'do goto auto void enum else break extern using asm case typeid wchar_t ' +
      'short reinterpret_cast|10 default double register explicit signed typename try this ' +
      'switch continue inline delete alignas alignof constexpr consteval constinit decltype ' +
      'concept co_await co_return co_yield requires ' +
      'noexcept static_assert thread_local restrict final override ' +
      'atomic_bool atomic_char atomic_schar ' +
      'atomic_uchar atomic_short atomic_ushort atomic_int atomic_uint atomic_long atomic_ulong atomic_llong ' +
      'atomic_ullong new throw return ' +
      'and and_eq bitand bitor compl not not_eq or or_eq xor xor_eq',
    built_in: '_Bool _Complex _Imaginary',
    _relevance_hints: COMMON_CPP_HINTS,
    literal: 'true false nullptr NULL'
  };

  const FUNCTION_DISPATCH = {
    className: "function.dispatch",
    relevance: 0,
    keywords: CPP_KEYWORDS,
    begin: concat(
      /\b/,
      /(?!decltype)/,
      /(?!if)/,
      /(?!for)/,
      /(?!while)/,
      hljs.IDENT_RE,
      lookahead(/\s*\(/))
  };

  const EXPRESSION_CONTAINS = [
    FUNCTION_DISPATCH,
    PREPROCESSOR,
    CPP_PRIMITIVE_TYPES,
    C_LINE_COMMENT_MODE,
    hljs.C_BLOCK_COMMENT_MODE,
    NUMBERS,
    STRINGS
  ];


  const EXPRESSION_CONTEXT = {
    // This mode covers expression context where we can't expect a function
    // definition and shouldn't highlight anything that looks like one:
    // `return some()`, `else if()`, `(x*sum(1, 2))`
    variants: [
      {
        begin: /=/,
        end: /;/
      },
      {
        begin: /\(/,
        end: /\)/
      },
      {
        beginKeywords: 'new throw return else',
        end: /;/
      }
    ],
    keywords: CPP_KEYWORDS,
    contains: EXPRESSION_CONTAINS.concat([
      {
        begin: /\(/,
        end: /\)/,
        keywords: CPP_KEYWORDS,
        contains: EXPRESSION_CONTAINS.concat([ 'self' ]),
        relevance: 0
      }
    ]),
    relevance: 0
  };

  const FUNCTION_DECLARATION = {
    className: 'function',
    begin: '(' + FUNCTION_TYPE_RE + '[\\*&\\s]+)+' + FUNCTION_TITLE,
    returnBegin: true,
    end: /[{;=]/,
    excludeEnd: true,
    keywords: CPP_KEYWORDS,
    illegal: /[^\w\s\*&:<>.]/,
    contains: [
      { // to prevent it from being confused as the function title
        begin: DECLTYPE_AUTO_RE,
        keywords: CPP_KEYWORDS,
        relevance: 0
      },
      {
        begin: FUNCTION_TITLE,
        returnBegin: true,
        contains: [ TITLE_MODE ],
        relevance: 0
      },
      // needed because we do not have look-behind on the below rule
      // to prevent it from grabbing the final : in a :: pair
      {
        begin: /::/,
        relevance: 0
      },
      // initializers
      {
        begin: /:/,
        endsWithParent: true,
        contains: [
          STRINGS,
          NUMBERS
        ]
      },
      {
        className: 'params',
        begin: /\(/,
        end: /\)/,
        keywords: CPP_KEYWORDS,
        relevance: 0,
        contains: [
          C_LINE_COMMENT_MODE,
          hljs.C_BLOCK_COMMENT_MODE,
          STRINGS,
          NUMBERS,
          CPP_PRIMITIVE_TYPES,
          // Count matching parentheses.
          {
            begin: /\(/,
            end: /\)/,
            keywords: CPP_KEYWORDS,
            relevance: 0,
            contains: [
              'self',
              C_LINE_COMMENT_MODE,
              hljs.C_BLOCK_COMMENT_MODE,
              STRINGS,
              NUMBERS,
              CPP_PRIMITIVE_TYPES
            ]
          }
        ]
      },
      CPP_PRIMITIVE_TYPES,
      C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      PREPROCESSOR
    ]
  };

  return {
    name: 'C++',
    aliases: [
      'cc',
      'c++',
      'h++',
      'hpp',
      'hh',
      'hxx',
      'cxx'
    ],
    keywords: CPP_KEYWORDS,
    illegal: '</',
    classNameAliases: {
      "function.dispatch": "built_in"
    },
    contains: [].concat(
      EXPRESSION_CONTEXT,
      FUNCTION_DECLARATION,
      FUNCTION_DISPATCH,
      EXPRESSION_CONTAINS,
      [
        PREPROCESSOR,
        { // containers: ie, `vector <int> rooms (9);`
          begin: '\\b(deque|list|queue|priority_queue|pair|stack|vector|map|set|bitset|multiset|multimap|unordered_map|unordered_set|unordered_multiset|unordered_multimap|array)\\s*<',
          end: '>',
          keywords: CPP_KEYWORDS,
          contains: [
            'self',
            CPP_PRIMITIVE_TYPES
          ]
        },
        {
          begin: hljs.IDENT_RE + '::',
          keywords: CPP_KEYWORDS
        },
        {
          className: 'class',
          beginKeywords: 'enum class struct union',
          end: /[{;:<>=]/,
          contains: [
            {
              beginKeywords: "final class struct"
            },
            hljs.TITLE_MODE
          ]
        }
      ]),
    exports: {
      preprocessor: PREPROCESSOR,
      strings: STRINGS,
      keywords: CPP_KEYWORDS
    }
  };
}

/*
Language: Arduino
Author: Stefania Mellai <s.mellai@arduino.cc>
Description: The Arduino® Language is a superset of C++. This rules are designed to highlight the Arduino® source code. For info about language see http://www.arduino.cc.
Website: https://www.arduino.cc
*/

/** @type LanguageFn */
function arduino(hljs) {
  const ARDUINO_KW = {
    keyword:
      'boolean byte word String',
    built_in:
      'KeyboardController MouseController SoftwareSerial ' +
      'EthernetServer EthernetClient LiquidCrystal ' +
      'RobotControl GSMVoiceCall EthernetUDP EsploraTFT ' +
      'HttpClient RobotMotor WiFiClient GSMScanner ' +
      'FileSystem Scheduler GSMServer YunClient YunServer ' +
      'IPAddress GSMClient GSMModem Keyboard Ethernet ' +
      'Console GSMBand Esplora Stepper Process ' +
      'WiFiUDP GSM_SMS Mailbox USBHost Firmata PImage ' +
      'Client Server GSMPIN FileIO Bridge Serial ' +
      'EEPROM Stream Mouse Audio Servo File Task ' +
      'GPRS WiFi Wire TFT GSM SPI SD ',
    _:
      'setup loop ' +
      'runShellCommandAsynchronously analogWriteResolution ' +
      'retrieveCallingNumber printFirmwareVersion ' +
      'analogReadResolution sendDigitalPortPair ' +
      'noListenOnLocalhost readJoystickButton setFirmwareVersion ' +
      'readJoystickSwitch scrollDisplayRight getVoiceCallStatus ' +
      'scrollDisplayLeft writeMicroseconds delayMicroseconds ' +
      'beginTransmission getSignalStrength runAsynchronously ' +
      'getAsynchronously listenOnLocalhost getCurrentCarrier ' +
      'readAccelerometer messageAvailable sendDigitalPorts ' +
      'lineFollowConfig countryNameWrite runShellCommand ' +
      'readStringUntil rewindDirectory readTemperature ' +
      'setClockDivider readLightSensor endTransmission ' +
      'analogReference detachInterrupt countryNameRead ' +
      'attachInterrupt encryptionType readBytesUntil ' +
      'robotNameWrite readMicrophone robotNameRead cityNameWrite ' +
      'userNameWrite readJoystickY readJoystickX mouseReleased ' +
      'openNextFile scanNetworks noInterrupts digitalWrite ' +
      'beginSpeaker mousePressed isActionDone mouseDragged ' +
      'displayLogos noAutoscroll addParameter remoteNumber ' +
      'getModifiers keyboardRead userNameRead waitContinue ' +
      'processInput parseCommand printVersion readNetworks ' +
      'writeMessage blinkVersion cityNameRead readMessage ' +
      'setDataMode parsePacket isListening setBitOrder ' +
      'beginPacket isDirectory motorsWrite drawCompass ' +
      'digitalRead clearScreen serialEvent rightToLeft ' +
      'setTextSize leftToRight requestFrom keyReleased ' +
      'compassRead analogWrite interrupts WiFiServer ' +
      'disconnect playMelody parseFloat autoscroll ' +
      'getPINUsed setPINUsed setTimeout sendAnalog ' +
      'readSlider analogRead beginWrite createChar ' +
      'motorsStop keyPressed tempoWrite readButton ' +
      'subnetMask debugPrint macAddress writeGreen ' +
      'randomSeed attachGPRS readString sendString ' +
      'remotePort releaseAll mouseMoved background ' +
      'getXChange getYChange answerCall getResult ' +
      'voiceCall endPacket constrain getSocket writeJSON ' +
      'getButton available connected findUntil readBytes ' +
      'exitValue readGreen writeBlue startLoop IPAddress ' +
      'isPressed sendSysex pauseMode gatewayIP setCursor ' +
      'getOemKey tuneWrite noDisplay loadImage switchPIN ' +
      'onRequest onReceive changePIN playFile noBuffer ' +
      'parseInt overflow checkPIN knobRead beginTFT ' +
      'bitClear updateIR bitWrite position writeRGB ' +
      'highByte writeRed setSpeed readBlue noStroke ' +
      'remoteIP transfer shutdown hangCall beginSMS ' +
      'endWrite attached maintain noCursor checkReg ' +
      'checkPUK shiftOut isValid shiftIn pulseIn ' +
      'connect println localIP pinMode getIMEI ' +
      'display noBlink process getBand running beginSD ' +
      'drawBMP lowByte setBand release bitRead prepare ' +
      'pointTo readRed setMode noFill remove listen ' +
      'stroke detach attach noTone exists buffer ' +
      'height bitSet circle config cursor random ' +
      'IRread setDNS endSMS getKey micros ' +
      'millis begin print write ready flush width ' +
      'isPIN blink clear press mkdir rmdir close ' +
      'point yield image BSSID click delay ' +
      'read text move peek beep rect line open ' +
      'seek fill size turn stop home find ' +
      'step tone sqrt RSSI SSID ' +
      'end bit tan cos sin pow map abs max ' +
      'min get run put',
    literal:
      'DIGITAL_MESSAGE FIRMATA_STRING ANALOG_MESSAGE ' +
      'REPORT_DIGITAL REPORT_ANALOG INPUT_PULLUP ' +
      'SET_PIN_MODE INTERNAL2V56 SYSTEM_RESET LED_BUILTIN ' +
      'INTERNAL1V1 SYSEX_START INTERNAL EXTERNAL ' +
      'DEFAULT OUTPUT INPUT HIGH LOW'
  };

  const ARDUINO = cPlusPlus(hljs);

  const kws = /** @type {Record<string,any>} */ (ARDUINO.keywords);

  kws.keyword += ' ' + ARDUINO_KW.keyword;
  kws.literal += ' ' + ARDUINO_KW.literal;
  kws.built_in += ' ' + ARDUINO_KW.built_in;
  kws._ += ' ' + ARDUINO_KW._;

  ARDUINO.name = 'Arduino';
  ARDUINO.aliases = ['ino'];
  ARDUINO.supersetOf = "cpp";

  return ARDUINO;
}

module.exports = arduino;
