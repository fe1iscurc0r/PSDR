# 上游 21 条 issue/PR 的原文存档（正文 + 全部评论）

抓取：2026-11-04，REST `GET /repos/MichaelRColton/PSDR/issues/{N}` 与 `/issues/{N}/comments?per_page=100`。
用途：**引用底稿**。这是别人的话，原文照录（只把连续空白压一下），**不代表本 fork 的判断**；
分析请看 `docs/PSDR-chronicle.md` 第一纪/第一纪补。要断言的强度：`原件`（GitHub 页面直接读到）。


---

## #1 [issue] Create Assembly Drawing for PSDR1

- 状态 closed｜开于 2014-07-15T12:55:44Z｜关于 2017-01-07T02:31:49Z｜作者 @MichaelRColton｜评论 1 条

**正文（@MichaelRColton）**

```
Some of the silk screens can be a little confusing, so an assembly drawing would be helpful.
```

**评论 @MichaelRColton｜2017-01-07T02:31:49Z｜id 271056763**

```
I probably won't bother with the drawings for the PSDR1 (if the three of you that have one really need one let me know!) but I did make instructions for the PSDR2.6. Find it here: https://github.com/MichaelRColton/PSDR/blob/PSDR_F7/Documentation/Assembly%20Instructions.pdf
```

---

## #2 [issue] Create PSDR1 Assembly Notes

- 状态 closed｜开于 2014-07-15T12:57:12Z｜关于 2017-01-07T02:34:38Z｜作者 @MichaelRColton｜评论 1 条

**正文（@MichaelRColton）**

```
This should include the changes to the PCB (VSS/VDD swap on MCU, and Grounds on DDS1-2) and all jumpers. Pictures wouldn't be a bad idea.
```

**评论 @MichaelRColton｜2017-01-07T02:34:38Z｜id 271056933**

```
Again, not going to bother at this point. If someone really needs them, let me know. Some documentation is available in the updates on the hackaday.io page here: https://hackaday.io/project/1538-portablesdr#menu-logs
```

---

## #3 [PR] Updated pin definitions and initializations.

- 状态 closed｜开于 2014-09-25T19:36:50Z｜关于 2014-09-29T21:40:09Z｜作者 @johnlaur｜评论 1 条

**正文（@johnlaur）**

```
These changes refactor the pin names, add a few missing pins, and more consistently initialize PSDR1 boards.
```

**评论 @johnlaur｜2014-09-29T21:40:09Z｜id 57234836**

```
I will create a new PR after merging PSDR2 stuff
```

---

## #4 [PR] Firmware Build Notes

- 状态 closed｜开于 2015-02-18T22:48:42Z｜关于 2016-01-03T20:05:00Z｜作者 @pwarren｜评论 0 条

**正文（@pwarren）**

```
Hope that's helpful!
```

---

## #5 [PR] Volume works, compiler warnings, newlib compilation

- 状态 closed｜开于 2016-12-31T05:28:34Z｜关于 2017-01-19T07:23:44Z｜作者 @pwarren｜评论 8 条

**正文（@pwarren）**

```
Hi Michael, my PSDR arrived on Thursday thanks :)

This PR adds changes to allow compilation on linux with newlib, fixes some of the easier compiler warnings from main.c and makes the volume menu item report the current AF gain setting * 10.

hope it's of use.
```

**评论 @pwarren｜2017-01-01T06:25:51Z｜id 269893557**

```
Ok, for 4b2fd07 I've added a bitmap for "Off" and made it call HAL_PWR_enterSTANDBYMode(), which should turn things down as far as it can go, hit the RESET button to power up again. May be a less brute force method of doing this!

PSDR.hex in 9308765 contains all changes :)
```

**评论 @pwarren｜2017-01-01T10:37:48Z｜id 269898385**

```
And in that one I tardown the peripheral's power before calling the StandBy function. Next step I'll work out how to scan for input changes while in this mode!
```

**评论 @MichaelRColton｜2017-01-03T05:00:34Z｜id 270052403**

```
AWESOME!

Give me a day or two to get these tested and merged back in. (I'm still a
little unskilled at some git operations)

You are my hero!

Your name sounds familiar (maybe because I've looked at the backer lists so
many times?) are you one of the people that built their own PSDR2s back
before it was on kickstarter?

Either way, thanks for your your work on this!

-Michael

On Sun, Jan 1, 2017 at 3:37 AM, Paul Warren <notifications@github.com>
wrote:

> And in that one I tardown the peripheral's power before calling the
> StandBy function. Next step I'll work out how to scan for input changes
> while in this mode!
>
> —
> You are receiving this because you are subscribed to this thread.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/pull/5#issuecomment-269898385>,
> or mute the thread
> <https://github.com/notifications/unsubscribe-auth/AHlbwr3duaqQIqrwfDC8iu-fv0W_wOTUks5rN4H-gaJpZM4LYfyW>
> .
>
```

**评论 @pwarren｜2017-01-03T06:19:12Z｜id 270057129**

```
Heh no worries, I'm concerned the newlib change might prevent builds with other toolchains (like on windows) but it's an easy revert.

I'm also not 100% on git and github. Had to delete my old fork, and re-fork to get the new branches, which I then worked off, but got there in the end!

You might recognise the name because I paid extra to have my extreme kit upgraded to a non-soldering one, and I did the linux build instructions a while ago. 

I've also updated the wiki with linux build instructions and left a comment on kickstarter :)
```

**评论 @fstkmaro｜2017-01-03T17:52:44Z｜id 270176950**

```
All, I hope all is well. Thanks for the continued work. Can this kit be acquired anymore? If so, where?

Thanks.

Sent from my iPhone

On Jan 3, 2017, at 1:19 AM, Paul Warren <notifications@github.com<mailto:notifications@github.com>> wrote:

Heh no worries, I'm concerned the newlib change might prevent builds with other toolchains (like on windows) but it's an easy revert.

I'm also not 100% on git and github. Had to delete my old fork, and re-fork to get the new branches, which I then worked off, but got there in the end!

You might recognise the name because I paid extra to have my extreme kit upgraded to a non-soldering one, and I did the linux build instructions a while ago.

I've also updated the wiki with linux build instructions and left a comment on kickstarter :)

-
You are receiving this because you are subscribed to this thread.
Reply to this email directly, view it on GitHub<https://github.com/MichaelRColton/PSDR/pull/5#issuecomment-270057129>, or mute the thread<https://github.com/notifications/unsubscribe-auth/AEBNq9XyJVugVmrIoFl9o8fiCnLSCqnFks5rOehhgaJpZM4LYfyW>.
```

**评论 @pwarren｜2017-01-03T23:20:59Z｜id 270253976**

```
in: 1381f544d076de45f68b465aa66a190966a1f321 looks like I wiped the .gitignore, apologies!

@fstkmaro I've no Idea, @MichaelRColton would probably know, seeing as it's his project!
```

**评论 @fstkmaro｜2017-01-04T00:02:02Z｜id 270260605**

```
thanks Paul

________________________________
From: Paul Warren <notifications@github.com>
Sent: Tuesday, January 3, 2017 6:21 PM
To: MichaelRColton/PSDR
Cc: fstkmaro; Mention
Subject: Re: [MichaelRColton/PSDR] Volume works, compiler warnings, newlib compilation (#5)

in: 1381f54<https://github.com/MichaelRColton/PSDR/commit/1381f544d076de45f68b465aa66a190966a1f321> looks like I wiped the .gitignore, apologies!

@fstkmaro<https://github.com/fstkmaro> I've no Idea, @MichaelRColton<https://github.com/MichaelRColton> would probably know, seeing as it's his project!

-
You are receiving this because you were mentioned.
Reply to this email directly, view it on GitHub<https://github.com/MichaelRColton/PSDR/pull/5#issuecomment-270253976>, or mute the thread<https://github.com/notifications/unsubscribe-auth/AEBNq8eh-moW2B5g8HfGXyvub9heeGy0ks5rOtfcgaJpZM4LYfyW>.
```

**评论 @MichaelRColton｜2017-01-13T02:42:42Z｜id 272346531**

```
Hi fstkmaro,

I'm still working out the details for building more of these. I can put you
on a list of people to contact if more become available, if you'd like.

On Tue, Jan 3, 2017 at 5:02 PM, fstkmaro <notifications@github.com> wrote:

> thanks Paul
>
>
>
> ________________________________
> From: Paul Warren <notifications@github.com>
> Sent: Tuesday, January 3, 2017 6:21 PM
> To: MichaelRColton/PSDR
> Cc: fstkmaro; Mention
> Subject: Re: [MichaelRColton/PSDR] Volume works, compiler warnings, newlib
> compilation (#5)
>
>
> in: 1381f54<https://github.com/MichaelRColton/PSDR/commit/
> 1381f544d076de45f68b465aa66a190966a1f321> looks like I wiped the
> .gitignore, apologies!
>
> @fstkmaro<https://github.com/fstkmaro> I've no Idea, @MichaelRColton<
> https://github.com/MichaelRColton> would probably know, seeing as it's
> his project!
>
> -
> You are receiving this because you were mentioned.
> Reply to this email directly, view it on GitHub<https://github.com/
> MichaelRColton/PSDR/pull/5#issuecomment-270253976>, or mute the thread<
> https://github.com/notifications/unsubscribe-auth/AEBNq8eh-
> moW2B5g8HfGXyvub9heeGy0ks5rOtfcgaJpZM4LYfyW>.
>
> —
> You are receiving this because you were mentioned.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/pull/5#issuecomment-270260605>,
> or mute the thread
> <https://github.com/notifications/unsubscribe-auth/AHlbwj4h_X0Cf3uO1uuzdA6fBaWXBLbwks5rOuF8gaJpZM4LYfyW>
> .
>
```

---

## #6 [issue] S meter pinned on USB with filter bottom at 0

- 状态 open｜开于 2017-01-06T12:05:03Z｜关于 None｜作者 @pwarren｜评论 2 条

**正文（@pwarren）**

```
S meter is pinned to halfway between +20 and +30 Db over 9. Moving the bottom of the filter up to '40' and it moves around with some bearing on the received signal! (PSDR_F7 branch)
```

**评论 @MichaelRColton｜2017-01-07T02:16:53Z｜id 271055853**

```
~~Are you saying it's always stuck there? On mine it moves around a lot (though the numbers don't correspond to anything yet.)~~ Just kidding, you are right, it does do that on USB. It didn't used to though, I'm not sure when I introduced that bug... (that part about the numbers remains true.
```

**评论 @pwarren｜2017-01-07T06:13:30Z｜id 271065990**

```
Heh ok, and I just noticed it doing the same thing on AM mode as well!
```

---

## #7 [issue] Project organisation: Licensing, Contributions etc

- 状态 closed｜开于 2017-01-06T12:15:48Z｜关于 2026-09-11T13:20:37Z｜作者 @pwarren｜评论 4 条

**正文（@pwarren）**

```
Figured I'd put up an issue for this.

I'd like to get a CONTRIBUTING.md file going, probably based on following https://mozillascience.github.io/working-open-workshop/contributing/

It would be a good idea to set the licensing terms for the code too, and make clear which parts are under which license (eg. GPLv2 or higher not appropriate for the shematics or gerbers, works for the code, but DSP_Lib is BSD(?) licensed, etc) 

Code layout and design, I've been very impressed by the code in the mCHF repos: https://github.com/df8oe/mchf-github, which may have some ideas for us! (In particular, I'm struggling with how to add FM mod/demod, including subaudible tones etc It's not clear to me from the current code, which may say more about me than the code!)
```

**评论 @jeffersonbenson｜2021-02-19T20:01:15Z｜id 782308153**

```
#15 seems to be accomplishing this, pending any necessary changes.
```

**评论 @fe1iscurc0r｜2026-08-19T05:01:48Z｜id 5337744605**

```
Hi Michael (and everyone on this thread),

I'm a university student and amateur radio enthusiast (recently passed my A-class ham license exam in China). I found PortableSDR through Hackaday and I'm genuinely impressed by the architecture — STM32F429 + dual AD9834 DDS + AD8302 VNA front-end is an elegant all-in-one design for portable QRP work.

I'd like to help move this thread forward: I'm interested in picking up development/maintenance on the repo. However, LICENSE.md still contains only "TODO: Determine the best license for this project", which means the code is technically all-rights-reserved — I can't legally fork, modify, or rebuild the hardware without explicit permission.

Would you consider choosing a license for the project? For a hardware + firmware project like this, common choices are:
- MIT (firmware/code)
- CERN-OHL or Solderpad (hardware designs/gerbers)
- GPL (if you prefer copyleft)

Even a short statement in LICENSE.md granting permission to fork and continue development would be enough to unblock us.

If you're no longer able to maintain it, I'd be happy to take over maintenance and keep the project alive — with full credit to you and the original authors. The radio deserves to live on.

Either way, thank you for designing and open-sourcing such a cool project.

Best regards,
Shen Zheyuan (fe1iscurc0r)
Radio amateur (A-class), Dalian, China
```

**评论 @jeffersonbenson｜2026-09-11T13:17:18Z｜id 5634997217**

```
@fe1iscurc0r Good morning!

I appreciate your interest in the project. At this time I don't think any of us are able to dedicate to the project in a full time capacity.

That being said, I believe there is still plenty to work off of and I personally would like to see the project continue to move forward.

I will see what I can do about adding an MIT license to the project to unblock you and please feel free to fork and help keep the project moving forward.

All the best,
Jeff
```

**评论 @MichaelRColton｜2026-11-03T01:47:22Z｜id 6593279486**

```
The MIT license is official — fully open (firmware, software, and hardware) has always been my intent for PortableSDR. Thanks @jeffersonbenson for getting it in and @fe1iscurc0r for the nudge. I've corrected the copyright line to name me and the project's contributors. Fork and build away. Closing this out.
```

---

## #8 [issue] Persistent state storage

- 状态 open｜开于 2017-01-06T12:18:45Z｜关于 None｜作者 @pwarren｜评论 1 条

**正文（@pwarren）**

```
It'd be nice to have the last used menu settings come back when the radio's turned on, with a way to reset it too I guess.

I'd imagine we'd need a menu state struct, which can be written to FLASH memory at some interval, maybe a second or so after a change?
```

**评论 @MichaelRColton｜2017-01-07T02:53:30Z｜id 271057939**

```
Agreed. Depending on what power state we drop down into, we may be able to preserve those things in memory without too much of a hit to standby current.
```

---

## #9 [issue] Proper Off menu item and 'Turn On' gesture

- 状态 open｜开于 2017-01-06T12:21:44Z｜关于 None｜作者 @pwarren｜评论 8 条

**正文（@pwarren）**

```
While my current implementation of an off button 'works' it doesn't seem to preserve the battery much more than a day or so.

Also, I need to figure out how to get the unit into a state that can monitor the buttons for the turn on gesture, I don't think my EnterSTANDBYMode() can do that, it appears to only be able to look for rising edges on the PA0 pin or interrupts.
```

**评论 @MichaelRColton｜2017-01-07T02:29:51Z｜id 271056639**

```
I haven't had time to look at or play with your new code yet, but I think I remember you mentioning turning off peripherals. Were you talking about those internal to the MCU, or the various external devices attached to the MCU?

I didn't design the PSDR with an eye for excellent standby efficiency (not that I don't want to, it just wasn't high on the list and I had other things to worry about) but I did include the ability to kill power to many of the sub systems on the board (via MCU controlled FETs), and some of the chips can be turned off by setting them to lower power states via whatever bus they are connected to.

I was pretty sure that the pins I used for the encoder switch, and maybe (hopefully!) the paddles supported pin change interrupts that should be able to wake the MCU, but I am not positive. Also potentially helpful would be slowing the clock way down, and setting up a routine that, for example, wakes the MCU on the first pin change event, then quietly watches for the other events in the gesture (whatever form that ends up taking) before bringing itself (and the other subsystems) up the rest of the way. If it doesn't see those other events within a certain time window, then it assumes that first event was unintentional and goes back to sleep.

I think the boards draw around 8mA (is that right?) before they are programmed, so that might be as low as we end up getting, but that should give 10ish days, which I think would be reasonable at this stage of development.
```

**评论 @pwarren｜2017-01-07T06:18:24Z｜id 271066164**

```
All I've done so far is do the opposite of the setupPeripheralPower() function, i.e: __GPIO_CLK_DISABLE() etc etc. then call HAL_PWR_EnterSTANDBYMode(). Not sure how much it helps, but It does recover when the reset button is pushed for at least a few hours after turning it off.

I should have a bit of time this week to look a things in a bit more depth for power management, after I get myself together for my https://linux.conf.au/ miniconf presentation. I'll definitely be showing off the PSDR while I'm there :)
```

**评论 @MichaelRColton｜2017-01-15T03:06:06Z｜id 272670234**

```
I made a mistake in my measurement before (I was using a different meter and misread it) so it draws ~80mA before it's programmed, and that's about what your turn-off code gets us down to.

Some thermal imaging shows that our biggest power consumption is the frequency synth chip (U241: SI5338). Pretty sure that can be powered down in code.

The LCD control circuitry is wasting some power (not sure if there is a command to power that down), not including the backlight. 

Also bad are the phase/mag chip (U314: AD8302), And the AD8131s (U260 and U253) and there isn't anything that can be done by the MCU to power them off.

Looks like I have some changes to make in the next rev.

We'll want to issue a command to put the SI5338 (and LCD if possible) into a lower power state, and then I don't think we'll get a whole lot lower than that.

And, of course, getting the wake-up gesture going. (P.S. Sometimes hitting reset didn't see to want to wake it, not sure why...)

Top side with LCD
![flir0289](https://cloud.githubusercontent.com/assets/7953346/21959939/623f8d38-da94-11e6-82bc-fd1a866c9b4d.jpg)
Top without LCD (that bright spot in the middle is the heat from the back of the SI5338)
![flir0290](https://cloud.githubusercontent.com/assets/7953346/21959941/624148f8-da94-11e6-8ca4-04d3c0d5d687.jpg)
Bottom
![flir0291](https://cloud.githubusercontent.com/assets/7953346/21959940/6240723e-da94-11e6-9497-6de8f7a4f14e.jpg)
```

**评论 @sanamon｜2017-01-18T21:30:22Z｜id 273607692**

```
I know it's not so high-tech, but perhaps an old-school switch between battery and radio would solve the problem? :-)
```

**评论 @jeffersonbenson｜2021-02-01T04:33:51Z｜id 770556698**

```
Gonna see if I can revive this thread :grin: 
Is the goal here to work something like (https://github.com/chacal/stm32sleep) where there is a low-power SLEEP state and then a WAKE gesture? 
Based on the circuitry, there isn't really a great way to completely disconnect the device from the battery. At this point it looks like the best we can do is get it to a low enough power state for short to medium-term storage, and then advise users to bring a spare battery pack?
```

**评论 @jeffersonbenson｜2021-02-04T17:47:56Z｜id 773490501**

```
To follow up on my above comment, couldn't you also just add a slide switch inline with the battery and have it poke out the "front" of the case, over by the rotary encoder? See below crude mockup:
![image](https://user-images.githubusercontent.com/19256220/106933579-158d6a80-66e7-11eb-8d50-353eda2dde81.png)
```

**评论 @sanamon｜2021-02-04T18:32:46Z｜id 773517766**

```
Hi,

I’m sure it’s the easiest route at least. 

But i’d start by looking into the preamp issue (preamp not enabled, perhaps by not bing initialized in software) as this thing is deaf as a brick right now (sensitivity around -70dBm if I remember correctly, indicating 50 dB “missing”)

Regards 
Jonas 

> 4 feb. 2021 kl. 18:48 skrev Jeff Benson <notifications@github.com>:
> 
> ﻿
> To follow up on my above comment, couldn't you also just add a slide switch inline with the battery and have it poke out the "front" of the case, over by the rotary encoder? See below crude mockup:
> 
> 
> —
> You are receiving this because you commented.
> Reply to this email directly, view it on GitHub, or unsubscribe.
```

**评论 @jeffersonbenson｜2021-02-04T22:52:00Z｜id 773655618**

```
@sanamon I see what you're saying with regards to the preamp issue. Perhaps something that can be brought up in a separate issue for further discussion?
For the issue at hand finding a compatible switch is the quickest way to power the whole device off.
```

---

## #10 [issue] Linux setup instructions

- 状态 closed｜开于 2017-01-11T22:28:55Z｜关于 2017-01-12T22:21:23Z｜作者 @sanamon｜评论 5 条

**正文（@sanamon）**

```
Hi,
Trying to setup the build environment for ubuntu 14.04.
Got eclipse installed including the addons. Checked out the project. 
But when trying to build, i get an error saying "fatal error: cstdlib: No such file or directory _cxx.cpp /PSDR/system/src/newlib line 13 C/C++ Problem"

Is there some other prereq that i've missed, or something else? Newbie to eclipse and to cross-compilation so any tips/ideas welcome!

Cheers, Jonas
```

**评论 @pwarren｜2017-01-11T22:48:32Z｜id 272020668**

```
Hi Jonas,

in PR #5, there's a commit to fix that: af4d1fa94eeb1e4b0ad401f3e1b09837f69a9066. Michael has not merged that into the project yet, and it may well break compilation with other toolchains.

It's a simple fix though, in Source/system/src/newlib/_cxx.cpp change the line
```#include <cstilb>```
to be
```#include <stdlib.h>```

And you should be good to go!
```

**评论 @sanamon｜2017-01-12T07:50:01Z｜id 272098646**

```
Thanks Paul!

I changed the line in _cxx.cpp from <cstdlib> to <stdlib.h>
but now the linker fails instead:

/usr/lib/gcc/arm-none-eabi/4.8.2/../../../arm-none-eabi/bin/ld: cannot find -lstdc++
collect2: error: ld returned 1 exit status

08:36:03 Build Finished (took 47s.892ms)

I'm sure it's just me who cant use the eclipse system...
Regards,
Jonas
```

**评论 @sanamon｜2017-01-12T22:21:13Z｜id 272302534**

```
I figured it out myself. It seems that for ubuntu 14.04 the **gcc-arm-none-eabi** package doesnt include the libstdc++ lib. A [known but unfixed](https://bugs.launchpad.net/ubuntu/+source/gcc-arm-none-eabi/+bug/1293024) bug apparently.

Fixed by manually downloading http://de.archive.ubuntu.com/ubuntu/pool/universe/libs/libstdc++-arm-none-eabi/libstdc++-arm-none-eabi-newlib_4.9.3+svn227297-1+8_all.deb and installing.

Now builds!
```

**评论 @sanamon｜2017-01-12T22:21:23Z｜id 272302576**

```
marked as closed
```

**评论 @sanamon｜2017-01-14T21:24:47Z｜id 272654238**

```
Update: could not build the project anyway. Had to de-install gcc-arm-none-eabi package and instead install gcc-arm-embedded following the instructions here: [link](https://launchpad.net/~team-gcc-arm-embedded/+archive/ubuntu/ppa)
```

---

## #11 [issue] Which tool was used to create the C arrays from the png images?

- 状态 closed｜开于 2017-01-23T17:35:06Z｜关于 2017-01-25T21:16:11Z｜作者 @sanamon｜评论 2 条

**正文（@sanamon）**

```
And is there a better way to communicate with other developers on the same projects, I suppose creating issues isnt the optimal way? I'm new to github and cannot find any way to send messages to other users?
```

**评论 @pwarren｜2017-01-24T10:49:04Z｜id 274769982**

```
For my OFF image, I used:
https://www.branah.com/text-to-image
to generate the PNG file. Then as per PSDR/Source/src/images.c I used http://www.rinkydinkelectronics.com/t_imageconverter565.php to get the C Array. Then I removed '0x00' Bytes from the end until it worked, I'm sure there's a method of calculating the padding correctly, but trial and error did work!

In terms of discussion, Michael's asked that we use github for now. The wiki could be used for some things too.

I did have a Discourse instance set up, but it has seen no use!
```

**评论 @sanamon｜2017-01-24T11:33:20Z｜id 274779994**

```
Thanks! :-)
Just what i wondered, my new "CW" mode image did not look as planned...

Regards,
Jonas

2017-01-24 11:49 GMT+01:00 Paul Warren <notifications@github.com>:

> For my OFF image, I used:
> https://www.branah.com/text-to-image
> to generate the PNG file. Then as per PSDR/Source/src/images.c I used
> http://www.rinkydinkelectronics.com/t_imageconverter565.php to get the C
> Array. Then I removed '0x00' Bytes from the end until it worked, I'm sure
> there's a method of calculating the padding correctly, but trial and error
> did work!
>
> In terms of discussion, Michael's asked that we use github for now. The
> wiki could be used for some things too.
>
> I did have a Discourse instance set up, but it has seen no use!
>
> —
> You are receiving this because you authored the thread.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/issues/11#issuecomment-274769982>,
> or mute the thread
> <https://github.com/notifications/unsubscribe-auth/ACWTixrO98e7a7IJN4Wn72_D4YZFYgZJks5rVdcigaJpZM4LrU7k>
> .
>
```

---

## #12 [PR] Added Contributing and License, reorganized Hardware

- 状态 closed｜开于 2021-01-18T21:56:02Z｜关于 2021-01-27T14:09:44Z｜作者 @jeffersonbenson｜评论 0 条

**正文（@jeffersonbenson）**

```
Added a basic template for the Contributing guide and a placeholder file for whenever a proper license can be determined. Also created the BOMs folder with subfolders for each version of the BOM. More clarity is needed to further organize the Hardware folder
```

---

## #13 [issue] Obsolete parts in 2.6.1 BOM

- 状态 open｜开于 2021-01-30T21:14:18Z｜关于 None｜作者 @jeffersonbenson｜评论 1 条
- labels: hardware

**正文（@jeffersonbenson）**

```
While compiling a BOM for an upcoming 2.6.1 build, I discovered that the following parts are obsolete according to Digikey and do not have replacements available. Further investigation will be required in order to find suitable replacement parts.

Parts not found:
599-1068-1-ND - RF amplifier U304
1465-1374-1-ND - RF DPDT Switch U16, U24, U30
```

**评论 @jeffersonbenson｜2021-02-19T16:46:23Z｜id 782195711**

```
Found the following outside of DigiKey, which is annoying but nevertheless it can be found

599-1068-1-ND - RF amplifier U304
SXB-2089Z
https://www.win-source.net/rf-amplifiers-sxb-2089z.html

1465-1374-1-ND - RF DPDT Switch U16, U24, U30
MASWSS0129TR-3000
https://www.richardsonrfpd.com/Products/Product/MASWSS0129
```

---

## #14 [issue] Missing parts in 2.6.1. BOM

- 状态 open｜开于 2021-01-30T21:18:13Z｜关于 None｜作者 @jeffersonbenson｜评论 3 条
- labels: hardware

**正文（@jeffersonbenson）**

```
The following parts are marked as either NA or DNS in the BOM. Have they just been removed and the BOM needs to be updated?

CAP_0603 - C307, C320
RES_0603 - R72, R79
```

**评论 @jeffersonbenson｜2021-02-19T18:45:55Z｜id 782267661**

```
So after learning a few things about reading BOMs, the NA seems to mean "just leave it open" and DNS means "do not stuff".

My only concern would be that there needs to be something to bridge the connections here like a 0ohm resistor or something. I'll need to investigate the traces.
```

**评论 @fe1iscurc0r｜2026-10-31T13:19:34Z｜id 6543885004**

```
Answering the open question in the follow-up comment: I checked the 2.6.1 netlist (extracted from the PADS Layout ASCII `Hardware/PSDR.asc` at `468dc41`), and **none of these four need a 0 ohm bridge**.

| part | pin 1 | pin 2 | what it is |
|---|---|---|---|
| C307 | U314.8 | GND | shunt cap to ground on one AD8302 pin |
| C320 | GND | U314.14 | same |
| R72 | `MIXER_LO2N` | `MIXER_LO2P` | across the two halves of the differential LO2 pair, in parallel with balun `L41` |
| R79 | `MIXER_LO1N` | `MIXER_LO1P` | same, in parallel with balun `L81` |

C307 and C320 are single-ended shunts to ground, so leaving them unpopulated removes nothing from any signal path. R72/R79 each sit across a differential LO pair that is already bridged by the balun winding in parallel, so an open there disconnects nothing - a 0 ohm part in that position would short the differential pair instead.

While checking this I also found a different BOM gap that this issue does not cover: parts that exist on the board but have no line in the BOM at all.

- The 2.6.1 BOM has 322 unique refdes; the board has 342 conventional refdes. 20 are on the board only:
 - 19 mechanical/placement parts: M1-M7 (mounting holes), X1/X2 (80 mil holes), F1-F6 (fiducials), CW1/CW2 (morse paddle contacts), DAC1/DAC2 (1 mm pads).
 - **R98** - a real omission. It is the series resistor between D101 (red LED) and U121 pin 43 (`LED_2`, PE13). BOM line 52 reads `R97,-99`, which expands to R97 and R99 only; it probably should be the range `R97-99`.
- `R6` and `R14` are listed twice: line 41 still says `R6,14,268` (qty changed from 3 to 1 in 2.6.1), while lines 42/43 add R6 (180R) and R14 (68R) separately. Line 41 should probably list only R268.
- The 2.6 BOM has the same 322 refdes as the 2.6.1 BOM, so all of the above predates 2.6.1.

The method is reproducible with `tools/pads_asc_netlist.py` (see #17). Happy to put together a BOM patch if that is useful.
```

**评论 @jeffersonbenson｜2026-10-31T16:58:37Z｜id 6546414010**

```
> Answering the open question in the follow-up comment: I checked the 2.6.1 netlist (extracted from the PADS Layout ASCII `Hardware/PSDR.asc` at `468dc41`), and **none of these four need a 0 ohm bridge**.
> 
> part pin 1 pin 2 what it is
> C307 U314.8 GND shunt cap to ground on one AD8302 pin
> C320 GND U314.14 same
> R72 `MIXER_LO2N` `MIXER_LO2P` across the two halves of the differential LO2 pair, in parallel with balun `L41`
> R79 `MIXER_LO1N` `MIXER_LO1P` same, in parallel with balun `L81`
> C307 and C320 are single-ended shunts to ground, so leaving them unpopulated removes nothing from any signal path. R72/R79 each sit across a differential LO pair that is already bridged by the balun winding in parallel, so an open there disconnects nothing - a 0 ohm part in that position would short the differential pair instead.
> 
> While checking this I also found a different BOM gap that this issue does not cover: parts that exist on the board but have no line in the BOM at all.
> 
> * The 2.6.1 BOM has 322 unique refdes; the board has 342 conventional refdes. 20 are on the board only:
> 
> * 19 mechanical/placement parts: M1-M7 (mounting holes), X1/X2 (80 mil holes), F1-F6 (fiducials), CW1/CW2 (morse paddle contacts), DAC1/DAC2 (1 mm pads).
> * **R98** - a real omission. It is the series resistor between D101 (red LED) and U121 pin 43 (`LED_2`, PE13). BOM line 52 reads `R97,-99`, which expands to R97 and R99 only; it probably should be the range `R97-99`.
> * `R6` and `R14` are listed twice: line 41 still says `R6,14,268` (qty changed from 3 to 1 in 2.6.1), while lines 42/43 add R6 (180R) and R14 (68R) separately. Line 41 should probably list only R268.
> * The 2.6 BOM has the same 322 refdes as the 2.6.1 BOM, so all of the above predates 2.6.1.
> 
> The method is reproducible with `tools/pads_asc_netlist.py` (see [#17](https://github.com/MichaelRColton/PSDR/pull/17)). Happy to put together a BOM patch if that is useful.

Please do!
```

---

## #15 [PR] Reorganization changes from PSDR_Rebuild

- 状态 closed｜开于 2021-02-01T03:14:01Z｜关于 2021-03-05T19:10:13Z｜作者 @jeffersonbenson｜评论 1 条
- labels: enhancement

**正文（@jeffersonbenson）**

```
This PR is to merge the changes made in the PSDR_Rebuild branch, complete with the schematics and BOM for v2.6.1. Additional changes include CONTRIBUTING and an updated README which will serve as the basis for the project's wiki pages.
```

**评论 @jeffersonbenson｜2021-03-05T19:10:03Z｜id 791622799**

```
Merging since sufficient time has elapsed to allow for comments
```

---

## #16 [issue] Enable Pre-Amp in Firmware

- 状态 open｜开于 2021-02-06T14:25:36Z｜关于 None｜作者 @jeffersonbenson｜评论 16 条
- labels: enhancement, help wanted

**正文（@jeffersonbenson）**

```
But i’d start by looking into the preamp issue (preamp not enabled, perhaps by not bing initialized in software) as this thing is deaf as a brick right now (sensitivity around -70dBm if I remember correctly, indicating 50 dB “missing”)
```

**评论 @DM2NT｜2021-12-06T10:23:30Z｜id 986638652**

```
I think Michael hasn't worked on this project for a long time. I also have a PSDR here. But like all the others, it's just a paperweight.
```

**评论 @MichaelRColton｜2021-12-06T17:23:13Z｜id 986988515**

```
It's true, I've become busy with other projects and the PSDR hasn't gotten
much of my time recently. Jeff is correct, the preamp/low-pass filter
circuit isn't working. I had it working on development hardware, but my
efforts to get it to operate properly on the production board didn't reach
completion. That would certainly be a great place to focus attention for
anyone that is interested in assisting with development.

On Mon, Dec 6, 2021 at 3:23 AM DM2NT ***@***.***> wrote:

> I think Michael hasn't worked on this project for a long time. I also have
> a PSDR here. But like all the others, it's just a paperweight.
>
> —
> You are receiving this because you are subscribed to this thread.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/issues/16#issuecomment-986638652>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AB4VXQSEGXSMECZW4CHCFJ3UPSFLFANCNFSM4XGKRASA>
> .
> Triage notifications on the go with GitHub Mobile for iOS
> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
> or Android
> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>
>
```

**评论 @DM2NT｜2021-12-06T18:45:40Z｜id 987058262**

```
Is it very complicated to activate the preamp? Unfortunately I don't have a Windows computer to run the development environment.
```

**评论 @MichaelRColton｜2021-12-07T20:29:42Z｜id 988242698**

```
Well in theory it shouldn't be too hard. Though it's certainly not as easy
as turning on power to it. There are RF switches that need to be
configured, and the pre-amp/low-pass filter IC has a lot of configuration
registers and things that have to be set correctly. The frustrating part is
that I had built one up on a dev board I made, ran some test code on it and
verified it was doing what I wanted (in this case, I was more focused on
the low-pass filtering part, but it did demonstrate the chip was working.)
but when I tried to do it on the production PSDR, I had trouble getting it
to work. I'm not sure what the problem is. And right now I just don't have
the bandwidth to work on it.

Most of my code is not in the main branch on github, btw, make sure you
look at them to see where the most recent activity is.

It might be worth putting on external pre-amp on the PSDR to see if it
performs better with that there. Where I live the bands are so noisy (S9+
most of the time) that the PSDRs sensitivity is actually fine, any signal
that can get through that shows up on the PSDR. I didn't realize at the
time that the sensitivity was a problem.

I am, by no means, an expert in RF/Radio design. If anyone makes
modifications that improve performance, I would love to know about them.

There is another project, called uSDR (there are some variations on it)
that pulls off pretty good performance with simpler circuitry than the
PSDR, and includes a very efficient amplifier design, something the PSDR
almost completely lacks. When I have some time, I'm interested in taking
what is (in my opinion) superior on the PSDR (the screen, processing power,
waterfall, ergonomics, case design, etc.) and merging in what I can from
the uSDR (simpler design, better sensitivity, better output power and
output filtering) into a next generation PSDR that could actually meet the
design goals I had for the original. But that may be a ways down the
line....

-Michael

On Mon, Dec 6, 2021 at 11:45 AM DM2NT ***@***.***> wrote:

> Is it very complicated to activate the preamp? Unfortunately I don't have
> a Windows computer to run the development environment.
>
> —
> You are receiving this because you commented.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/issues/16#issuecomment-987058262>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AB4VXQU6E7CUSKHJIO5FUG3UPUAF7ANCNFSM4XGKRASA>
> .
> Triage notifications on the go with GitHub Mobile for iOS
> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
> or Android
> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>
>
```

**评论 @DM2NT｜2021-12-09T15:21:29Z｜id 989951651**

```
Hi Michael,

I also know the uSDX. Unfortunately, it doesn't offer a good display interface. I don't want to do without the waterfall display. Andreas DF8OE has already implemented the HMC1023 in his UHSDR. Here is the link to the Github: https://github.com/df8oe/UHSDR/tree/active-devel/mchf-eclipse/hardware

Maybe you can already use a part here.
However, I still don't have a Windows computer ...
```

**评论 @petermccracken｜2021-12-09T16:16:13Z｜id 990001249**

```
... I think a Malahit is what you want, either the original or there is one of the china clones which is as good as the original. There's a very active group of FB. Also google teensy convolution sdr if you really want to get into it.
```

**评论 @petermccracken｜2021-12-09T16:20:52Z｜id 990005553**

```
Also have a look at the mcHF group on FB, if you look through the posts there's a Russian guy who is selling modified kits for the mcHF with a 4" display, looks very good. There are heaps of possibilities and projects out there.
```

**评论 @MichaelRColton｜2021-12-09T16:30:09Z｜id 990013738**

```
DM2NT, Yes, I agree the uSDX interface is lacking (and in my opinion, the
ergonomics, case design, and the microcontroller is very underpowered,
thought they've managed to do an impressive amount with it) the idea I'm
playing with is merging the PSDR and the uSDX, but it will be a while, or
may never happen at all. Also, you don't need a Windows computer to work on
the PSDR, I just don't have instructions for other environments. Any guide
on doing STM32 development for your platform will likely work.

Peter, the Malahit looks pretty cool, but looks like it has rather
different goals from what I hope the PSDR eventually becomes. I am aware of
the mcHF, it's a nice project for sure. Interestingly, KA7OEI, the guy that
overhauled the mcHF, hugely improved its software (and maybe hardware too?)
lives not far from me and I've talked to him about the PSDR. He said he's
willing to take a look at it, but we haven't really made it happen yet.

-Michael

On Thu, Dec 9, 2021 at 9:21 AM petermccracken ***@***.***>
wrote:

> Also have a look at the mcHF group on FB, if you look through the posts
> there's a Russian guy who is selling modified kits for the mcHF with a 4"
> display, looks very good. There are heaps of possibilities and projects out
> there.
>
> —
> You are receiving this because you commented.
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/issues/16#issuecomment-990005553>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AB4VXQW3CJJC2OHQCVVDIZLUQDJO5ANCNFSM4XGKRASA>
> .
> Triage notifications on the go with GitHub Mobile for iOS
> <https://apps.apple.com/app/apple-store/id1477376905?ct=notification-email&mt=8&pt=524675>
> or Android
> <https://play.google.com/store/apps/details?id=com.github.android&referrer=utm_campaign%3Dnotification-email%26utm_medium%3Demail%26utm_source%3Dgithub>.
>
>
```

**评论 @sanamon｜2022-07-04T18:55:08Z｜id 1174082898**

```
> Unfortunately I don't have a Windows computer to run the development environment.

You dont need windows to do this. If You have a Linux machine, see https://github.com/MichaelRColton/PSDR/wiki/Linux-build-instructions

Cheers,
Jonas
```

**评论 @DM2NT｜2025-10-28T08:07:12Z｜id 3455087742**

```
Hello Michael.

How many PSDRs have you actually sent out?
Would it be worth working on the software again after all these years?
I still think the form factor is a unique selling point of the PSDR to this day.
Unfortunately, some components are no longer available here in Europe. But I would be absolutely thrilled if we could get the preamble, filter, and TX/RX working with SSB. I don't need any more features.
```

**评论 @MichaelRColton｜2025-10-28T15:42:12Z｜id 3457156033**

```
Hi!

How many were sent out? I guess it depends on how you count them (some
people ordered kits without components, did they ever build them?) but it's
about 100 units (surprisingly, there were a few people that never sent
their address, despite repeated requests, and two that shipped out and were
returned by the shipping company)

Would it be worth working on the software? I'm not sure, I would love for
it to be closer to reaching its potential. On the other hand, I'd like to
update the design with things I've learned since then to make it better.
But that will take time I don't currently have. It's one of those projects
that I should just set aside an hour a week and chip away at it until it
gets done. I can't promise anything right now. But if anyone else wants to
contribute I would love that and will support it.

As for parts, if there are particular parts you are missing, let me know, I
do still have a lot of that.

-Michael

On Tue, Oct 28, 2025 at 2:07 AM DM2NT ***@***.***> wrote:

> *DM2NT* left a comment (MichaelRColton/PSDR#16)
> <https://github.com/MichaelRColton/PSDR/issues/16#issuecomment-3455087742>
>
> Hello Michael.
>
> How many PSDRs have you actually sent out?
> Would it be worth working on the software again after all these years?
> I still think the form factor is a unique selling point of the PSDR to
> this day.
> Unfortunately, some components are no longer available here in Europe. But
> I would be absolutely thrilled if we could get the preamble, filter, and
> TX/RX working with SSB. I don't need any more features.
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/MichaelRColton/PSDR/issues/16#issuecomment-3455087742>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/AB4VXQXCFQE7OB4JVEW7AZT3Z4P4NAVCNFSM6AAAAACKNCOOH2VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTINJVGA4DONZUGI>
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>
```

**评论 @DM2NT｜2025-10-30T19:02:28Z｜id 3469639763**

```
Hi Michael.

I sent you an email about the components. I'm not sure if the email address is still active, though. Unfortunately, the MASWSS0129 parts are no longer available here. If you happen to have any...
```

**评论 @fe1iscurc0r｜2026-11-03T01:20:28Z｜id 6592865486**

```
Paper check only - I read the published board data (netlist extracted from `Hardware/PSDR.asc`, the 2.6.1 BOM) and both firmware trees. No hardware in front of me, so nothing below is a measurement, and I am not attaching a PR - just asking before anyone writes code.

**1. The RF gain block in the antenna chain does not look like an HF part.**

`Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv` line 75 reads `1,599-1068-1-ND,,,,,,,1` - it carries the DigiKey number, but the manufacturer and MPN cells were empty in the shipped file (PR #18 proposes filling them; the MPN came from the hyperlink stored inside `PSDR2.6.1_BOM.xls`, which points at RFMD `SXB-2089Z`).

The SBB/SXB-2089 family is documented as **50-850 MHz**: the SIRENZA datasheet title for SBB-2089 is literally "50 - 850 MHz, Cascadable Active Bias InGaP/GaAs HBT MMIC Amplifier", and Qorvo's page for SBB2089Z lists min 50 MHz / max 850 MHz, 20 dB, NF 2.7 dB, 5 V / 90 mA, SOT-89. That is a cellular-band gain block. In a 0.1-35 MHz receiver it should provide no gain at all. If the SXB variant differs from SBB2089Z, that is exactly the thing worth confirming.

**2. The footprint name points at a different part, and the bias network points back at a 5 V part.**

The pad name in the board netlist for U304 is `MMIC-AMP_HMC482ST`. HMC482ST89 is DC-5 GHz (so HF-capable) but requires **+6 to +12 V**, while this board feeds the node from `+5V_AMP`:

```
RF_AMP_IN = BIAS.1 + C13.2 + L11.1 (220uH) + U304.1 (RFIN)
RF_AMP_OUT = C305.2 + L19.1 (220uH) + U304.3 (RFOUT)
L11 -> RF_AMP_IN ; R6 (180R) ties +5V_AMP into that node
```

So the bias looks like it was re-laid for a 5 V part and the footprint name is a leftover. Does that match what you remember populating on the boards you sent out?

**3. The firmware never routes through that position either.**

`Source_F7/src/main.c`, `signalPath()` (:823). All three implemented cases write the same relay state, and it is the bypass state:

```
:838 / :873 / :906 AMP_SWITCH_A = 0, AMP_SWITCH_B = 1
```

:906 sits under the comment `//Amp relay set to on` (:905), while the other two sit under `//Amp relay set to bypass`. The older F4 tree sets the same pin inline and documents the levels: `Source/src/main.c:958` writes `1 //Route through amp`, `:967` writes `0 //Bypass amp`. And the TX caller uses `signalPath(transmit_no_amp_no_filter)` at :1103, with the `transmit_with_amp_no_filter` call on :1104 commented out.

To keep this precise about what it costs: baseband gain after the mixers does exist (`U255`/`U272` = MCP6N11 instrumentation amps, gain set by `U15` = MAX5388), so the radio is not amplifier-less. What it has no example of is RF gain ahead of the mixers, which is the part that buys noise figure and image rejection.

**Two questions, no PR attached:**

- Is `AMP_SWITCH_A = 0` at :906 a slip for `1`, or was the "with amp" path never actually routed?
- Which part is really in U304 on built boards? If it is a 50-850 MHz gain block, then the "sensitivity around -70dBm, indicating 50 dB missing" symptom in your first comment has two separate causes, and the HF one is a part change (a DC-starting 5 V SOT-89 gain block), not a register write.

This pass over the data was done with AI assistance. Every citation above is a file and line in this repo, so please treat anything I got wrong as fixable rather than settled.
```

**评论 @fe1iscurc0r｜2026-11-03T05:05:41Z｜id 6595930419**

```
One correction on my own citations - the substance above is unchanged.

I quoted the F7 side from my fork's path `Source_F7/src/main.c`. This repo has no `Source_F7/` directory; on the F7 branches the file is `Source/src/main.c`. After the branch-layout note in #19 I re-checked both F7 branches, and all three points hold in **both** - only the line numbers differ (`PSDR_Rebuild` tip `b9c0629`, `PSDR_F7` tip `ab2c8fd`):

| claim | `PSDR_Rebuild` `Source/src/main.c` | `PSDR_F7` `Source/src/main.c` |
|---|---|---|
| `AMP_SWITCH_A = 0` / `AMP_SWITCH_B = 1` in the three implemented cases | :838 / :873 / :906 | :833 / :868 / :901 |
| comment `//Amp relay set to on` immediately followed by that same bypass pattern | :905-906 | :900-901 |
| TX caller uses `transmit_no_amp_no_filter`, with the `transmit_with_amp_no_filter` call commented out | :1103-1104 | :1139-1140 |

For provenance: my mirror is blob-identical to `PSDR_Rebuild` (`main.c` = `def78a44`, `i2c.c` = `619f2f5e`), so the numbers I gave are correct for that branch - they just needed the branch named.

The two questions stand as written: is `AMP_SWITCH_A = 0` under the "set to on" comment a slip for `1`, and which gain block is actually populated in U304 on the boards that went out? If it is an SBB/SXB-2089 (50-850 MHz), then the HF half of the sensitivity complaint is a part-selection matter, not a register write - and a DC-starting 5 V gain block would be the direction to look at, since the footprint name here (`MMIC-AMP_HMC482ST`, DC-5 GHz) points at exactly that class, except that it wants +6 to +12 V while the board supplies `+5V_AMP`.
```

**评论 @fe1iscurc0r｜2026-11-03T14:35:25Z｜id 6606601865**

```
Two corrections to my own earlier comments here, plus one number worth measuring.

**1. The "50-850 MHz" attribution was the wrong part.**

I wrote that "the SBB/SXB-2089 family is documented as 50-850 MHz" and asked whether the SXB variant differs. It does, so that sentence was wrong as applied to U304:

- 50-850 MHz is **SBB2089Z** - "50MHz to 850MHz, CASCADABLE ACTIVE BIAS InGaP HBT MMIC AMPLIFIER" (DS130718), a 5 V gain block.
- The part the BOM's own hyperlink points at is **SXB-2089Z**, which third-party copies of DS110610 title "5MHz to 2500MHz MEDIUM POWER InGaP/GaAs HBT AMPLIFIER", tested at Vs=8V / RBIAS=20 ohm / VDEVICE=5.2V, 120-135-150 mA.

So "a cellular-band gain block that should provide no gain below 50 MHz" describes SBB2089Z, not the purchased part, and my HF half of the diagnosis loses its main support. I am not replacing it with the 5-2500 MHz figure either, because I could not verify that at source: Qorvo has removed the product page (https://www.qorvo.com/products/p/SXB-2089Z is 404 and the legacy rfmd.com path redirects to the homepage), so DS110610 currently exists for me only as mirror text. What survives of the original point, and what I would still like confirmed: which marking is actually on populated boards, and whether the bias network was built for an 8 V / RBIAS part while the board supplies +5V_AMP.

**2. "R6 (180R)" - the board file says 100R, and 2.6 to 2.6.1 changed more resistors than I thought.**

180 R is the 2.6.1 BOM value (RHM180DCT-ND); `Hardware/PSDR.asc` records `Value 100R` for R6. That sent me checking every designator across board file vs both BOMs: 339 joined, 255 agree, **11 disagree** (R6, R14, R68, R69, R72, R75, R76, R79, R113, R164, R268). Also, 2.6 to 2.6.1 is not just R164 270K to 240K - R6 100R to 180R and R14 100R to 68R change in the same direction, and the board file still carries the 2.6 values for all three. Mine is a data-consistency observation, not a claim about your boards; only a multimeter or your memory settles which source is authoritative.

**3. The 3 V3 rail may be ~2.9-3.0 V, which is tight for the RF switch control inputs.**

`+3V3_CPU` comes from the AP3417C (U114) with FB divider R113 (top, to the rail) / R112 = 100K (to GND). The Diodes sheet, DS36516 Rev. 3-3 - which I downloaded and hash-verified myself - gives "Feedback Voltage: 600mV" and a setting table whose 3.3 V row is 450K/100K. The board has 383K (board file) or 402K (2.6.1 BOM) on top, so the rail should sit at **0.6 x (1 + R1/R2) = 2.90 V or 3.01 V**, not 3.3 V. A mirror of MASWSS0129 Rev V6 states its control high level as +2.9 V to +5 V. If both are right, the GPIO driving those switches has roughly 0.1 V of margin - and on the development hardware you verified, the logic rail may well have been different from the production board's.

So a cheap check on any working unit: measure `+3V3_CPU` at U114's output, and the voltage actually appearing on U16/U24/U30 control pins. If the rail is at 2.9-3.0 V and the MCU drives to it, "the preamp/LPF circuit isn't working on the production board" may partly be switches that never fully turn.

One pointer, now file-level rather than a tree link (DM2NT already pointed at UHSDR in 2021): the HMC1023 driver lives at `mchf-eclipse/hardware/uhsdr_hmc1023.c`, e.g. commit c447c2e4 "Finalized the finalized HMC1023 driver :-)" (2018-10-21). For reference on what such a driver must satisfy: the register set uses a coarse bandwidth code of 5/7/10/14/20/28/40/50/72 MHz, a calibration clock of 20-80 MHz with duty within 50% +/- 10%, and writing any bit of register 04h starts a calibration cycle.

Written with AI assistance; the corrections are mine. Everything above is checkable from the repo (netlist, BOM, `Hardware/PSDR.asc`) or from the two vendor documents named.
```

**评论 @fe1iscurc0r｜2026-11-04T05:17:38Z｜id 6623233867**

```
**Self-correction on item 2 of my earlier comment** - same two .xls files, but I had the fact and the inference the wrong way round.

I wrote "2.6 to 2.6.1 ... R6 100R to 180R and R14 100R to 68R change in the same direction". Re-reading both unmodified files through a spreadsheet importer, cell by cell (2.6: 41,472 B, BIFF sha256 `076a7098...`; 2.6.1: 39,424 B, `020f17df...`), this is what the tables actually contain:

| file | sheet row (item_no. 41) | ref_des | qty_per_unit | vendor_part_# | value |
|---|---|---|---|---|---|
| 2.6 | 45 | `R6,14,268` | 3 | `P100GCT-ND` | 100R |
| 2.6.1 | 45 | `R6,14,268` | **1** | `P100GCT-ND` | 100R |
| 2.6.1 | 46 | `R14` | 1 | `RHM68DCT-ND` | 68R |
| 2.6.1 | 47 | `R6` | 1 | `RHM180DCT-ND` | 180R |

So the shipped 2.6.1 BOM assigns R6 two values and R14 two values **inside one file**. The qty column makes the intent legible: row 45's qty_per_unit was already cut from 3 to 1, which only makes sense once R6 and R14 moved out into rows 46/47 - the number was updated, the designator text was not. That is a half-applied edit, not a version delta.

Checking that convention mechanically: in each file, 43 rows list more than one name in ref_des. In 2.6.1 exactly three of them disagree with their own qty_per_unit - row 5, which is a header row whose cell lists net names (`-,+,CLK,IO,NRST`) rather than designators, so it is not really a group; row 45 above; and row 56 `R97,-99`, where qty says 3 but the text names R97 and R99 while R97/R98/R99 are all three on the board, so R98 has no line. In 2.6 the same check finds two: row 5 and row 54, which is the same `R97,-99` row. The two non-header disagreements are precisely the two edits PR #18 makes.

Why it matters for anyone diffing the versions mechanically: "R6 100R -> 180R" is an inference from rows 46/47, not a statement the table makes. A script reading 2.6.1 as shipped sees both 100R and 180R for R6, and which one it reports depends on iteration order.

What does not change from my earlier comment: `Hardware/PSDR.asc` records `Value 100R` for both R6 and R14 (the 2.6 value), the 11 board-file-vs-BOM disagreements stand, and only a multimeter or your memory settles which source is authoritative. PR #18's row-45 edit only removes the duplicated names from the text - it asserts no value, and I am not proposing one for either resistor.
```

---

## #17 [PR] Add a KiCad schematic for PSDR 2.6.1 generated from the PADS netlist

- 状态 closed｜开于 2026-10-31T13:13:09Z｜关于 2026-11-03T21:33:57Z｜作者 @fe1iscurc0r｜评论 1 条

**正文（@fe1iscurc0r）**

```
## What this adds

The repo only ships PADS binaries for the schematic (`Hardware/PSDR.sch`), which no open-source tool can read. This PR adds a KiCad 10 schematic for PSDR 2.6.1 whose connectivity is generated mechanically from the PADS Layout ASCII, so the netlist is authoritative instead of being traced from a PDF.

- `dist/kicad/PSDR_2.6.1.kicad_sch` + `-p02..p10`: 10 sheets, 391 symbols, 57 symbol definitions in `PSDR_2.6.1.kicad_sym`
- `dist/netlist/PSDR_2.6.1_netlist.{csv,json}`: 278 nets / 1132 connected pins
- `tools/pads_asc_netlist.py`: PADS ASCII → netlist
- `tools/pads_asc_to_kicad.py`: netlist + PDF page layout → `.kicad_sch` (deterministic UUIDs, regeneration is byte-identical)
- `tools/kicad_netlist_compare.py`, `tools/kicad_sch_geomcheck.py`: the two checks below
- `Hardware/PSDR.asc`: byte-identical copy of the 2.6.1 PADS Layout ASCII that already exists on `PSDR_Rebuild` / `PSDR_F7` / `PSDR_F7_DMA` at `468dc41` (blob `115cf19`). Added here so master can regenerate the netlist without checking out another branch.
- `Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`: byte-identical copy of `Hardware/PSDR Schematic.pdf` at `468dc41` (blob `5390527`), renamed because master's file of that name (blob `bdf02d2`) is a different, older 2014 design — overwriting it would lose that file.

## What this is not

It is not a redrawn schematic. Wires are not drawn: every pin carries a global label at the pin endpoint, and those labels carry the connectivity. The artwork follows the 2.6.1 PDF's 10-page layout, one sheet per page. Treat it as a machine-checkable netlist you can open in KiCad, not as a schematic to read the way you read the PDF.

## Verification

- Netlist equality: exported KiCad XML vs the PADS netlist, compared as a partition of pins (catches shorts, not just name differences): 278/278 nets identical, 1132/1132 pins covered, 0 nets on one side only, 0 pins in more than one net, 391 components.
- Geometry: no two connection points coincide in any of the 10 sheets (1173 points = 1132 labels + 41 no-connects). Checked separately because KiCad silently merges coincident pins and the netlist export cannot reveal it.
- ERC: 0 errors, 391 warnings, all `footprint_link_issues` — no footprint library is shipped on purpose.
- Regeneration from a clean clone is byte-identical apart from the `Footprint` property (`--pcb` is optional).
- Net names: 276/278 identical; the other two differ only by the PADS overbar escape (`AUDIO_AMP_\SHDN` → `AUDIO_AMP_~{SHDN}`).

## Known limits

- 11 one-pin test pads have ambiguous refdes text in the PDF (`+`, `-`, `1PPS`, `CLK`, `DAC1`, `DAC2`, `GND`, `LIPO`, `NRST`, `SCL`, `SDA`); they sit in a strip at the bottom of their sheet. Connectivity is unaffected — the netlist is keyed by refdes, not by position.
- No hierarchical sheet pins; global labels handle cross-sheet connectivity.
- No footprints, hence no PCB. A board file is deliberately excluded.

Happy to split this up — e.g. the netlist tooling only — if 1.6 MB of PADS ASCII in the repo is not what you want.
```

**评论 @fe1iscurc0r｜2026-11-01T04:23:32Z｜id 6553367174**

```
Since this PR deliberately stops at the schematic, the board is **not** part of its diff. For completeness, here is what the same PADS ASCII yields when carried through to a four-layer KiCad PCB — a probe on my fork, commit [`418f0a5`](https://github.com/fe1iscurc0r/PSDR/commit/418f0a5031b07af50811e69dd860f6759d523a46):

**Generated board**: 4 copper layers, 278 nets, 391 parts, 1194 pads (1132 carry a net), 5034 track segments, 22 arcs, 419 vias. Four stdlib-only tools under `tools/` (decal parser, route parser, emitter, plus two reconciliation scripts), deterministic output (regenerating gives a byte-identical file).

**Two independent checks against the 2.6.1 release Gerbers** (`Hardware/Gerbers/PSDR261 Main Board/`):

- every D03 flash in the source Gerber has a matching KiCad flash on the same layer within 0.0066 mil (0.17 µm);
- the KiCad-side flash count on each layer is accounted for exactly as "pads on that layer + 419 vias" — no unexplained copper.

**Drill**: 460 of 461 holes match by diameter. The one miss is a 3.2 mm hole at (582.70, 2167.30) mil, and the root cause is in the source decal: J170 numbers its four mounting holes `PAD 20/21/22/23` while its terminals are `21/22/23/24`, so `PAD 20` is never referenced and `T24` falls through to a default pad. The drill file has 4 holes; the decal has 4 but only 3 are referenced. Production should follow the drill file.

**Not a production board yet**: no copper pours (12 `POUROUT` regions over 7 nets; GND consequently has 20 unconnected items), `Edge.Cuts` is the 100.0 × 65.0 mm envelope rather than the real 258-piece outline, and no silkscreen. DRC: 309 violations + 20 unconnected — 199 are the expected missing-footprint-library notices (footprints are embedded in the board), 52 are real clearance items under the default 0.2 mm rule (minimum measured 0.1174 mm), and 14 are NPTH holes tangent to pads by design in J170/J153.

Happy to keep this separate, or open it as its own PR if a generated board is of interest.
```

---

## #18 [PR] Fix BOM Ref Des typos (R98, R6/R14), record the four DNP parts (#14) and their manufacturer part numbers (#13)

- 状态 open｜开于 2026-11-01T12:46:28Z｜关于 None｜作者 @fe1iscurc0r｜评论 2 条

**正文（@fe1iscurc0r）**

```
## What this changes

**Reviewing without Excel:** `Hardware/BOMs/PSDR_2.6.1/BOM_changes_PR18.md` (added in the last commit)
lists every changed cell - 13 cells across the two workbooks, with before/after text, the full text
of the four long notes, what did not change, and the one known side effect of re-saving a legacy
`.xls`. It is generated from a cell-by-cell UNO dump of `master` and this branch, so it can be
checked against the binaries rather than trusted.

Three BOM repairs, each backed by something already present in this repository.

**1. Ref Des fixes (un-orderable rows)**

| File | Item | Cell | Before | After |
|---|---|---|---|---|
| `PSDR2.6.1_BOM.xls` | 41 | R45C2 | `R6,14,268` | `R268` |
| `PSDR2.6.1_BOM.xls` | 52 | R56C2 | `R97,-99` | `R97-99` |
| `PSDR2.6_BOM.xls` | 50 | R54C2 | `R97,-99` | `R97-99` |

`R6`/`R14` were already listed on their own rows, so the old text double-counted them; `R97,-99` dropped R98, which is a real part (see the 2.6.1 schematic PDF, `Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`).

**2. Record of why `C307,320` and `R72,79` are DNP (issue #14)**

#14 asks whether these four were removed and whether the BOM needs updating. The 2.6.1 netlist extracted from the board itself (PADS Layout ASCII `Hardware/PSDR.asc` at `468dc41`, via `tools/pads_asc_netlist.py`: 391 parts / 278 nets / 1132 pins):

| part | pin 1 | pin 2 | role |
|---|---|---|---|
| C307 | `$$$2472` (other pin: U314.8 only) | GND | shunt |
| C320 | GND | `$$$2458` (other pin: U314.14 only) | shunt |
| R72 | `MIXER_LO2N` (also C71.2, L41.1) | `MIXER_LO2P` (also C73.2, L41.6) | bridge |
| R79 | `MIXER_LO1N` (also C78.2, L81.1) | `MIXER_LO1P` (also C80.2, L81.6) | bridge |

**None of the four is a series element**, so removing any of them breaks no connection and **no 0 ohm jumper is needed** -- which answers the open question in the follow-up comment on #14. For R72/R79 the opposite matters: both nets already reach the LO winding, so fitting 0 ohm there would short the pair. All four still have footprints, pads and silkscreen designators on the board, so this is "not fitted by design", not "removed".

The reason the rows read like missing data: `OPEN` and `DNS` were written in the **Value** column. Nothing here overwrites existing cells -- the notes go into the unlabelled column you already use for assembly remarks (J in the 2.6.1 sheet, L in the 2.6 sheet; 9 rows already live there, e.g. "Buy but do not populate").

**3. Manufacturer part numbers behind issue #13**

The two devices in #13 can be identified from inside this repository, so they are written down before the DigiKey SKUs are the only thing left to search.

| row | DigiKey | filled | authority |
|---|---|---|---|
| `U304` | `599-1068-1-ND` | `Mfg` = RF Micro Devices (RFMD), `Mfg Part #` = `SXB-2089Z` | the row's own hyperlink: `https://www.digikey.com/product-detail/en/rfmd/SXB-2089Z/599-1068-1-ND/937042`, plus your note on the same row ("Name mismatch is okay, The Digikey part # is the correct part") and the matching note `*Not the part listed in Type` on the equivalent 2.5 row (U19). So the `Type` / decal name `MMIC-AMP_HMC482ST` is a stale label. |
| `U16,U24,U30` | `1465-1374-1-ND` | `Mfg Part #` = `MASWSS0129TR`; **`Mfg` left blank** | no hyperlink on this row (only 8 of 89 rows carry one) and no author disclaimer, so the value is copied from the sheet's own `Type` / PADS `*PARTTYPE*` string. We are not asserting a vendor from a name alone. |

The same two rows in `OctopartBOM.csv` are filled likewise -- 83 of its 85 rows already had Manufacturer + MPN, and these two were the only blanks.

## Verification

The workbooks were edited through LibreOffice UNO by a script that resolves each row from its Ref Des cell, refuses to write unless the target cell is empty, and restores the source font and column widths. Cell-by-cell dump against the preceding commit: **2 added cells per workbook for the DNP notes, then 3 added cells per workbook for the manufacturer numbers, plus the `.xls` column-width rounding (1-2 storage units per column) -- nothing else**. Yellow fill (`0xffff00`) and `Arial 10` are preserved, and all 8 row hyperlinks survive the re-save (BIFF8 keeps them in a UTF-16 stream; that is where the `SXB-2089Z` mapping came from). `OctopartBOM.csv` differs on exactly 2 lines.

## Deliberately not included

- No replacement or substitute part is proposed for anything in this PR, and no claim is made that either device is currently available anywhere.
- "Obsolete" itself is not verifiable from repository data: `OctopartBOM.csv` carries In Stock / MOQ / price per distributor but **no lifecycle or status column**, so this PR only records identities.
- The structural weakness this exposes -- the sheet is indexed by DigiKey SKU, and `Mfg` / `Mfg Part #` were filled on only 5 of 89 rows -- is worth fixing across the whole BOM, but that would touch most rows and is left as separate work.

## Note on merge order

This single PR covers #14 and #13 on purpose: both edit the same two binary `.xls` workbooks, which git cannot auto-merge, so splitting them into two pull requests would create a guaranteed conflict for you to resolve by hand. Commit order is `9c3ca93` (Ref Des) -> `fa5e336` (DNP record) -> `48b838e` (manufacturer numbers), so each concern can still be reviewed as its own commit.

> Made with AI assistance. The netlist extraction, the cell-patch script and the dump comparison are reproducible; commands and outputs are recorded in this fork's build log `docs/WO-psdr-takeover.md`, sections C-7, G-1, G-2 and G-3.
```

**评论 @jeffersonbenson｜2026-11-03T21:35:16Z｜id 6615994815**

```
Are alternatives also suggested as part of this PR? Or is it only calling out what needs to be fixed?
```

**评论 @fe1iscurc0r｜2026-11-04T04:14:47Z｜id 6622367887**

```
It fixes; there are no alternative parts in it, deliberately.

The changes are cells - 13 of them, listed one by one in `BOM_changes_PR18.md` so a binary `.xls` diff can be reviewed without Excel. Three are worth naming:

- `R97,-99` -> `R97-99`, in both BOMs. That row's own Qty column says 3 while the text names two designators, and R97/R98/R99 are all on the board - so R98 had no line.
- The 2.6.1 row `R6,14,268` (Qty **1**, 100R) now lists only `R268`. This one is more than formatting: in the shipped file it sits directly above separate rows `R6` = 180R (`RHM180DCT-ND`) and `R14` = 68R (`RHM68DCT-ND`). **The same 2.6.1 BOM gave R6 two values and R14 two values.** Splitting the row removes a contradiction inside one file.
- C307/C320/R72/R79: the reasons those four are DNP go into the BOM's own unlabelled notes column, so the answer to #14 lives in the file, in the column the author already used for exactly that kind of note.

For #13, `Mfg`/`Mfg Part #` are filled only where the file carries evidence for them: U304's own embedded DigiKey hyperlink points at RFMD `SXB-2089Z` (and that row already says "Name mismatch is okay, The Digikey part # is the correct part"), which also explains its stale footprint name `MMIC-AMP_HMC482ST`. For `U16,24,30` I filled `MASWSS0129TR` and deliberately left `Manufacturer` blank - that row has no hyperlink, so the part type name is all the shipped data supports.

No substitutes, on purpose: U304 is a 3-pad part and the DPDTs are 13-pad, so any replacement moves footprint and bias network - a board redesign, not a BOM edit. And "obsolete" is not something the shipped data can prove; `OctopartBOM.csv` has no lifecycle column. Two leads from today, stated as observations: from this machine `cdn.macom.com/datasheets/MASWSS0143.pdf` and `MASWSS0202.pdf` return 200 (twice each, curl and browser) while `MASWSS0129.pdf` returns 404 both ways, and Qorvo's site no longer surfaces an SXB-2089Z page for us.

One consequence of the split, which is arguably also "what needs to be fixed": once R6 and R14 have only their own rows, 2.6 -> 2.6.1 turns out to have changed three resistor values, not one - `R164` 270K -> 240K (already known), plus `R6` 100R -> 180R and `R14` 100R -> 68R - while `Hardware/PSDR.asc` still carries the 2.6 value for all three, and disagrees on eight more designators (R113 383K against 402K in both BOMs; R68/R69/R75/R76 and R268 as 1k0 against 0R/100R; R72/R79 as 1k0 against DNP). Happy to open a separate issue with that list if you would rather keep it out of this thread - settling it needs a board and a meter, which is not something I want to resolve by editing data.

Reply written with AI assistance from the repo's own files; the cell-level claims above are checkable against `Hardware/BOMs/PSDR_2.6.1/` and `Hardware/PSDR.asc`.
```

---

## #19 [issue] Two firmware spots that may stop a board from booting (F7 main loop, Si5338 I2C wait) - opinion before any PR

- 状态 open｜开于 2026-11-02T13:14:50Z｜关于 None｜作者 @fe1iscurc0r｜评论 3 条

**正文（@fe1iscurc0r）**

```
Context: I am rebuilding the 2.6.1 design in a fork (KiCad board, BOM, manufacturing data) and did a **read-only** survey of the firmware so I could document it. I have not modified any source file, and I am not sending a PR - you may have reasons for these two spots. Asking for your opinion first.

## 1. `Source_F7/src/main.c:1021-1032` - debug loop before the real main loop

The committed F7 source has an unconditional `while(1)` that only fills the screen black/blue, and it sits *before* the real main loop at line 1065. Nothing in that block exits or is wrapped in `#if 0`, so in this source state the real loop is unreachable. It looks like a leftover from the DMA/display debugging (the "this DMA thing is killing me" period).

If you agree, the minimal change is to delete or disable that block. Everything after it (the `initAdc`/`updateDisplay`/`setGainPot` sequence) then runs as intended.

## 2. `Source_F7/src/frequency_control.c:54-55` - I2C wait without a timeout

```c
while(result!= HAL_OK)
 result = HAL_I2C_IsDeviceReady(&handleI2C, (0x70 << 1), 100, 100);
```

There is no bound on the retries. If the Si5338 does not acknowledge (missing part, bad I2C pull-ups, stuck bus - the file already has a `clearStuckBusyFlag` helper for that), the boot never reaches the display initialisation. A bounded retry (say a few hundred ms) followed by continuing without the synthesiser, with the failure shown on screen, would make a dead synthesiser a visible fault instead of a silent hang.

## Not a request, just a finding that affects #16

Mapping the low-pass filter path for the same survey: the firmware contains **no reference to the HMC1023 (U287)** at all - no SPI configuration, and no drive for the `LPF_POWER` line (PE11) that gates the filter's 5 V switch (Q208). While checking the pinout against the netlist extracted from `Hardware/PSDR.asc`, one thing looked off: **U287 pin 28 (`VDDBG`) is connected only to a decoupling capacitor (C292) and has no 5 V supply**, while the datasheet describes that pin as the bias 5 V supply. Please double-check that against the schematic - if the netlist is right, that path cannot work no matter what the firmware does, and it is a board change rather than a software one. (Pin 29 `VBG` is described as a 1.2 V bandgap *test* output, so leaving it open is fine.)

## Where the evidence is

- Survey with file:line references, module notes and a defect list: `https://github.com/fe1iscurc0r/PSDR/blob/next/docs/PSDR-firmware-survey.md`
- HMC1023 pin/net/SPI table and the `VDDBG` note: `https://github.com/fe1iscurc0r/PSDR/blob/next/docs/PSDR-HMC1023-netlist.md`
- The netlist itself is extracted from `Hardware/PSDR.asc` at `468dc41` by a small script in the same fork; the command is in the document.

Would you like a PR with only the two minimal changes above (no other edits), or would you prefer to leave the firmware as it is for now?

> Made with AI assistance for the code reading and netlist extraction; every finding above is reproducible from the repository, and I have not run the board.
```

**评论 @MichaelRColton｜2026-11-03T02:43:36Z｜id 6594095941**

```
@fe1iscurc0r A quick heads-up on branches, to save you effort. The repo's branch layout is a bit tangled right now:

- `master` currently holds the older **STM32F4** code.
- The firmware survey you did (the `Source_F7/` tree with the dead `while(1)` before the main loop and the unbounded Si5338 I²C wait) looks like it came from the DMA-development lineage.
- My newest F7 branch, **`PSDR_F7`** (the STM32F746 target these boards actually run), has neither of those: the debug loop is commented out and the I²C code in `i2c.c` is structured differently.

So **`PSDR_F7` is the tree to base firmware work on**. I've just gotten it building headless from the command line again, and I'm using it as the base for the HMC1023 LPF bring-up. I'll also tidy up the branch layout so this is less confusing for everyone.

Your survey was genuinely useful regardless — the HMC1023 VDDBG netlist finding (pin 28 with no 5 V) is a real board bug, and the mux/bypass mapping was correct. Thanks for digging in.

-Michael
```

**评论 @fe1iscurc0r｜2026-11-03T05:06:27Z｜id 6595940378**

```
Thanks for the pointer - it corrected one of my assumptions. I checked the branches instead of guessing (read-only; blob ids so we mean the same tree).

**1. You are right about the display trap.** `PSDR_F7:Source/src/main.c:1020-1045` goes straight from the display setup into `Adafruit_GFX_setTextSize(3)`, and the only live `while(1)` is :1101, the real main loop. `PSDR_Rebuild:Source/src/main.c:1021-1032` still has the unconditional `while(1) { fillScreen(BLACK); fillScreen(BLUE); }` ahead of the main loop - so **P0-1 is specific to `PSDR_Rebuild`**, and my survey should have named the branch.

**2. One correction on lineage.** The tree I reviewed is not the DMA lineage: my mirror is blob-identical to `PSDR_Rebuild` (`main.c` = `def78a44`, `i2c.c` = `619f2f5e`), while `PSDR_F7_DMA` (`457c270`) has `main.c` = `f5a41214`. The dates also explain how the two got confused: `PSDR_Rebuild`'s tip is the 2021-01-27 merge of PR #12 (`b9c0629`), `PSDR_F7`'s tip is 2018-07-31 (`ab2c8fd`) - so "newest" depends on whether you mean the branch you keep working on or the last commit timestamp.

**3. P0-2 is still present in `PSDR_F7`; it only moved files.** `PSDR_F7:Source/src/main.c:1031-1032`:

```c
while(result!= HAL_OK)
 result = HAL_I2C_IsDeviceReady(&handleI2C, (0x70 << 1), 100, 100);
```

No trial count or timeout escape in that loop, so if the Si5338 does not answer, boot stops there - before display and ADC init, same symptom as Rebuild's `frequency_control.c:53-54`. The `i2c.c` reorganisation you mention is real (`PSDR_F7` and `PSDR_F7_DMA` share blob `c3e49239`, 825 lines; `PSDR_Rebuild` splits it into a 138-line `i2c.c` + `frequency_control.c` + `si5338.c`), it just did not remove this wait. Since the HMC1023 bring-up is on `PSDR_F7`, that branch will hit the same wall on any board where the synthesiser is slow to answer.

Two questions so we do not collide with your work:

- Is `PSDR_F7` (`ab2c8fd`) the canonical firmware base, and `PSDR_Rebuild` superseded? And would a bounded retry (N trials, then report and continue) be acceptable **in principle** on `PSDR_F7`? If yes, I will not spend effort patching two trees. Still opinion only - no PR attached.
- Should my `Source_F7/` mirror be re-based onto `PSDR_F7`? My honest read is that re-basing costs a full re-run of my build reconciliation and buys little unless the two trees are meant to converge, so I would rather you decide than have me guess - especially since that is where you are working.

And noted with thanks on `VDDBG`. If it helps the bring-up I can drop the whole U287 pin/net table into a comment here: SPI on PB12-PB15 (`SEN`/`SCK`/`SDI`/`SDO`, shared bus with the MAX5388 gain pot, separated by `FILTER_CS` and `GAIN_POT_NSS` on PE4), `CALCK` coupled from Si5338 CLK1A via C283, and `LPF_POWER` on PE11 feeding a P-MOSFET that no firmware path drives. Say the word.

Read with AI assistance; every number above is one `git grep` away.
```

**评论 @fe1iscurc0r｜2026-11-03T08:20:30Z｜id 6598776381**

```
Follow-up on the base: I re-based my F7 mirror onto `PSDR_F7` and the port cost nothing, so this is mainly a "there is a command-line build you can use" note. No PR attached.

Measured on `PSDR_F7 @ ab2c8fd` with `arm-none-eabi-gcc` 13.2.1 (Linux), using our makefile with no rule changes:

```
make -f Makefile.linux -j4 rc=0, 0 errors, 0 undefined references, 26 warnings
text 114068 data 18488 bss 18260
```

Vector gate against the hex committed on your own branch (`Source/Debug/PSDR.hex`, blob `e6fe1975`, last touched `aaa24f8`, 2017-01-15):

```
initial SP 0x20050000 agrees
empty slots [7, 8, 9, 10, 13, 95] agrees
reset built 0x080001D5 vs ref 0x080002F9 (reported, not gated - the layout moves with
 toolchain/linker, same situation as on F4)
RESULT: PASS
```

It passes against the older `457c270` (2018-06-21) hex too, which is why both are kept as references with sha256 / blob id / provenance in `dist/reference/README.md`.

Two things that may save you a minute each:

1. **No source edits were needed on this branch.** On the mirror I had before (`PSDR_Rebuild`) the build needed two small include fixes in `si5338.c` / `frequency_control.c` to get through GCC 13. Those two files do not exist on `PSDR_F7` (the Si5338 driver lives inside the 825-line `src/i2c.c`), so our entire F7-side delta is now `Makefile.linux` plus one `.gitignore` line - `git diff --numstat upstream/PSDR_F7:Source <mirror>` reports exactly that, and no `.c/.h` change.

2. **Your Eclipse Debug config excludes 42 files under `system/src/stm32f7-hal`** (`.cproject` line 232; `hal_dma.c` is among them, while `hal_i2c/uart/tim/spi/adc/dac/gpio/rcc` are kept) **and it does not exclude `src/TinyGPS.c`.** Our harness compiles the HAL without that list and skips TinyGPS.c. I measured all three policies deliberately:

```
this harness (all HAL, no TinyGPS.c) text 114068 data 18488 bss 18260
follow the .cproject (TinyGPS.c compiled) text 114064 data 18488 bss 18260
follow the .cproject (+ those 42 exclusions) text 114064 data 18488 bss 18260
```

With `--gc-sections` all three build clean and converge to the same size, so the superset here is a convenience rather than a hidden behavioural difference - but I would rather state it than let this look like a byte-for-byte reproduction of your Eclipse output. (Sizes match; byte-identity is not claimed and not tested.)

I could not find a makefile anywhere on `PSDR_F7` - the branch tracks `PSDR.ioc`, `.cproject`, `.project`, and `Source/Debug/` only the hex - so if your command-line build is not committed yet, ours is here, with the flags and the exclusion differences documented in its header: https://github.com/fe1iscurc0r/PSDR/blob/next/Source_F7/Makefile.linux

Carrying over from my earlier comment: the fill-screen trap is indeed not on this base (confirmed, and our defect list dropped it), and the unbounded `while(result != HAL_OK) HAL_I2C_IsDeviceReady(...)` loop is, at `Source/src/main.c:1031-1032`. Also still standing from the hardware side: `U287` pin 28 `VDDBG` has no 5 V, so that path needs a board change, not a register write.

Say the word about what you want done with any of this and I will follow your lead. Read, built and measured with AI assistance.
```

---

## #20 [issue] Are the VNA and filtered signal paths implemented anywhere? signalPath() has four empty stubs - question, no PR

- 状态 open｜开于 2026-11-03T01:25:20Z｜关于 None｜作者 @fe1iscurc0r｜评论 1 条

**正文（@fe1iscurc0r）**

```
This is a question, not a PR proposal, and it comes from reading `Source_F7/src/main.c` plus the 2.6.1 board netlist. I have no hardware here, so nothing below is a measurement.

`enum signalPaths` (:811-820) declares seven states. Only three have code:

```
0 recieve_no_filter implemented
1 recieve_with_filter empty
2 transmit_no_amp_no_filter implemented
3 transmit_with_amp_no_filter implemented (see #16 about its relay state)
4 tramsmit_with_amp_with_filter empty (the enum name is misspelled)
5 vna_reflected empty
6 vna_through empty
```

The `default:` branch is commented out (:937-940), so an unexpected value silently leaves every relay where it was.

The two VNA cases are the ones I care about, because the impedance bridge + `U314` (AD8302) is the part of this radio that nothing else at this size does, and the hardware side of it looks complete and already routed:

```
ANT/VNA-IN.1 -> C303 -> U16 (amp bypass DPDT) -> C21 -> U24 (bridge in/out DPDT)
 -> C27 -> U30 (RF port DPDT) -> C306 -> RF_REF -> VNA-OUT.1

RF_REF = C306.1 C322.1 R28.1 R321.2 REF.1 VNA-OUT.1
RF_ANT = C309.1 DUT.1 R29.1 R308.2
U314 AD8302: INPA <- C322, INPB <- C309
```

So `vna_reflected` presumably means: set `IMP_BRIDGE_SWITCH_A/B` to insert the bridge and `TX_RF_SWITCH_A/B` to route to the VNA-OUT SMA. The MCU pins are all there and already driven in the three implemented cases (`IMP_BRIDGE_SWITCH_A` = U121.16 / PC1, `IMP_BRIDGE_SWITCH_B` = U121.30 / PA6, `TX_RF_SWITCH_A` = U121.36 / PB2, `TX_RF_SWITCH_B` = U121.31 / PA7).

Same shape of gap on the filter selector: `FILTER_S0`/`FILTER_S1` appear only three times (:856-857, :891-892, :924-925) and every one writes the same bypass state, even though the board exposes four 0.1 inch header pads (`E_FILT_IF_P/N`, `E_FILT_RF_P/N`) that are already one position of `U211`/`U298` (74CBTLV3253). A plug-in band-pass bank was accounted for in hardware and no code path ever selects it. (Schematic/pad evidence only; I am not proposing a filter design here.)

You wrote in #16 (2021-12-07): "Most of my code is not in the main branch on github, btw, make sure you look at them to see where the most recent activity is." So the cheapest possible answer is a pointer:

1. Is there a branch or development tree that already contains the VNA relay states, the filtered RX/TX cases, or the HMC1023 register setup?
2. If yes, could you name the ref? That would save anyone from reverse-engineering switch polarities out of comments that say "(I think!)".
3. If no, then these four stubs are the honest to-do list, and I would like to keep them written down somewhere public.

Read with AI assistance; every citation above is a file and line in this repo.
```

**评论 @fe1iscurc0r｜2026-11-03T05:05:08Z｜id 6595923321**

```
A correction on my own citations - the findings do not change.

The line numbers in the body above come from my fork's layout, where the F7 tree sits at `Source_F7/src/main.c`. This repo has no `Source_F7/` directory: on the F7 branches the file is `Source/src/main.c`. After Michael's note in #19 about the branch layout I re-checked both F7 branches, and every claim above holds in both - only the coordinates differ:

| claim | `PSDR_Rebuild` `Source/src/main.c` (tip `b9c0629`) | `PSDR_F7` `Source/src/main.c` (tip `ab2c8fd`) |
|---|---|---|
| `enum signalPaths`, seven states | :811-820 | :806-815 |
| empty cases `tramsmit_with_amp_with_filter` / `vna_reflected` / `vna_through` | :928 / :931 / :934 | :923 / :926 / :929 |
| `default:` commented out | :937-940 | :932-935 |
| `FILTER_S0`/`FILTER_S1` writes, all three the same `(1,0)` | :856-857 / :891-892 / :924-925 | :851-852 / :886-887 / :919-920 |
| TX/RX call sites (TX uses `transmit_no_amp_no_filter`, the `with_amp` call commented out) | :1103-1104, RX :1115 | :1139-1140, RX :1151 |

Provenance, so the branch is unambiguous: my `Source_F7/` mirror is blob-identical to `PSDR_Rebuild` (`main.c` = `def78a44`, `i2c.c` = `619f2f5e`), which is the branch I quoted.

So the substance stands: four of the seven `signalPaths` cases are empty in **both** F7 branches, and neither VNA case ever sets `IMP_BRIDGE_SWITCH_A/B` or `TX_RF_SWITCH_A/B`. Sorry for the path confusion.

Housekeeping: this got filed twice by accident - the duplicate is #21, now closed; keeping this one.

Read with AI assistance.
```

---

## #21 [issue] Are the VNA and filtered signal paths implemented anywhere? signalPath() has four empty stubs - question, no PR

- 状态 closed｜开于 2026-11-03T01:25:34Z｜关于 2026-11-03T05:04:06Z｜作者 @fe1iscurc0r｜评论 0 条

**正文（@fe1iscurc0r）**

```
This is a question, not a PR proposal, and it comes from reading `Source_F7/src/main.c` plus the 2.6.1 board netlist. I have no hardware here, so nothing below is a measurement.

`enum signalPaths` (:811-820) declares seven states. Only three have code:

```
0 recieve_no_filter implemented
1 recieve_with_filter empty
2 transmit_no_amp_no_filter implemented
3 transmit_with_amp_no_filter implemented (see #16 about its relay state)
4 tramsmit_with_amp_with_filter empty (the enum name is misspelled)
5 vna_reflected empty
6 vna_through empty
```

The `default:` branch is commented out (:937-940), so an unexpected value silently leaves every relay where it was.

The two VNA cases are the ones I care about, because the impedance bridge + `U314` (AD8302) is the part of this radio that nothing else at this size does, and the hardware side of it looks complete and already routed:

```
ANT/VNA-IN.1 -> C303 -> U16 (amp bypass DPDT) -> C21 -> U24 (bridge in/out DPDT)
 -> C27 -> U30 (RF port DPDT) -> C306 -> RF_REF -> VNA-OUT.1

RF_REF = C306.1 C322.1 R28.1 R321.2 REF.1 VNA-OUT.1
RF_ANT = C309.1 DUT.1 R29.1 R308.2
U314 AD8302: INPA <- C322, INPB <- C309
```

So `vna_reflected` presumably means: set `IMP_BRIDGE_SWITCH_A/B` to insert the bridge and `TX_RF_SWITCH_A/B` to route to the VNA-OUT SMA. The MCU pins are all there and already driven in the three implemented cases (`IMP_BRIDGE_SWITCH_A` = U121.16 / PC1, `IMP_BRIDGE_SWITCH_B` = U121.30 / PA6, `TX_RF_SWITCH_A` = U121.36 / PB2, `TX_RF_SWITCH_B` = U121.31 / PA7).

Same shape of gap on the filter selector: `FILTER_S0`/`FILTER_S1` appear only three times (:856-857, :891-892, :924-925) and every one writes the same bypass state, even though the board exposes four 0.1 inch header pads (`E_FILT_IF_P/N`, `E_FILT_RF_P/N`) that are already one position of `U211`/`U298` (74CBTLV3253). A plug-in band-pass bank was accounted for in hardware and no code path ever selects it. (Schematic/pad evidence only; I am not proposing a filter design here.)

You wrote in #16 (2021-12-07): "Most of my code is not in the main branch on github, btw, make sure you look at them to see where the most recent activity is." So the cheapest possible answer is a pointer:

1. Is there a branch or development tree that already contains the VNA relay states, the filtered RX/TX cases, or the HMC1023 register setup?
2. If yes, could you name the ref? That would save anyone from reverse-engineering switch polarities out of comments that say "(I think!)".
3. If no, then these four stubs are the honest to-do list, and I would like to keep them written down somewhere public.

Read with AI assistance; every citation above is a file and line in this repo.
```