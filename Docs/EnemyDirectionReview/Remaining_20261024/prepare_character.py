"""Prepare a single authorized character's image prompts and explicit anatomical plan in Docs."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
inventory=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))
name=sys.argv[1]
t=next(t for t in inventory['targets'] if t['name']==name)
family=Path(t['controller']).parent.name
identities={
'BugQueen':'Large low-backed golden-brown insect queen, tiny oval plated head, enormous domed segmented abdomen with luminous orange-gold round nodules and pale highlights, six short ochre armored legs ending in dark points. Back shell dominates its silhouette. No wings, pincers or stinger.',
'Bull':'Stocky dark olive-brown bull with ochre spots, large ivory upward horns, broad cream muzzle and four split hooves; thin tail with tuft.',
'BullMounted':'The original dark olive-brown spotted bull with ivory horns wears a small gold-brown leather saddle, girth, metal buckle and stirrup. There is NO rider.',
'BullyRooster':'Tall dark olive rooster, huge orange-gold lobed comb and wattles, golden face ring and beak, dark curled tail feathers, dark folded wings and two golden clawed feet.',
'Bunny':'Cream-white rabbit with ochre cheek and flank spots, huge upright ears, buck teeth, small cotton tail and large rounded hind paws; four paws, low quadruped posture.',
'Burro':'Ochre-brown donkey with very long upright ears, cream muzzle and belly, spotted coat, four hooves and thin tufted tail.',
'Butcher':'Stocky olive-gray ogre butcher with pale chef hat, apron, stitches, heavy metal left forearm guard and a broad notched cleaver in his RIGHT hand. Two legs and two arms, no tail.',
'Cannibal':'Stocky ochre skinned ogre with dark short hair and chin beard, pointed ears, primitive golden fur/leather loincloth, skull belt and a spiked golden wooden club in his RIGHT hand.',
'Caterpillar':'Low golden-ochre caterpillar with large rounded segmented back, sleepy dark outlined head and six tiny ochre walking feet.',
'CaveCaterpillar':'Olive-brown rounded segmented caterpillar, golden eye, angular cream crystal shards embedded on its back, six short cream-and-brown feet. Preserve the crystals.',
'CaveRat':'Small white shaggy rat with ochre patches, amber eye, round ears, four short clawed feet and long pale ringed tail.',
'Cerberus':'Dark brown THREE-HEADED canine with ochre spots, golden dorsal spikes, collar and hanging metal chain, four paws and thin curved tail. All three distinct heads remain visible and turn consistently; no extra bodies.',
'Chick':'Round golden yellow chick with tiny orange crest and beak, large cream eyes, short wings, two small three-toed yellow feet and small tail feathers.',
'Chicken':'Round cream-white chicken with ochre patches, small ochre crest and beak, two short wings, small tail feathers and two yellow feet.',
'Cow':'Stocky white cow with ochre spots, cream muzzle, two small ivory horns, dark ears, four hooves and thin white tail with dark tip.',
'Crawler':'Legless low golden-brown segmented crawler, triangular cream and gold spikes along its back, sleepy head with zigzag mouth. No invented legs or wings.',
'CrystalLizard':'Small gold lizard with amber eye, four splayed short clawed feet, long pointed tail and angular ochre crystal spikes down back and tail.',
'DarkBunny':'Dark gray-olive rabbit with gold patches, huge long upright ears with cream edges, buck teeth, four paws, small fluffy tail.',
'Donkey':'Gray-tan donkey with ochre patches and pale dots, huge upright ears, cream muzzle, four hooves, thin tail with dark tuft.',
'Drake':'Ochre-gold duck with spiky golden head feathers, ivory neck ring, broad orange bill, short folded wings, small tail and two webbed feet.',
'DreadEye':'Floating olive-gold spherical single-eyed monster with TWO large leathery bat wings. One huge ivory eye on the front; its rear is a closed shell without an eye. No legs or tail.',
'Dreadnought':'Gray-olive muscular armored ogre with gold mohawk, angular dark armor, spiked shoulder, broad belt and a long notched dark sword in his RIGHT hand.',
'Duck':'Cream-white duck with ochre cheek and body patches, small white crest, wide orange bill, two white wings, short tail and two orange webbed feet.',
'EvilEye':'Floating gold spherical single-eyed monster with two ochre bat wings, one huge ivory front eye and small curved mouth; rear has no eye. No legs or tail.',
'FancyParasite':'Golden sluglike segmented parasite with a broad circular tooth-filled mouth, two rows of ivory teeth, faceted gold crystal studs on top, tapering rear. No legs.',
'FlyingDemon':'Floating dark olive-brown spiked spherical cyclops with one ivory and amber eye and a huge fang-filled mouth. Its original visible design has NO wings, legs or tail.',
'ForestTurkey':'Ochre-brown turkey with golden neck and wattle, broad rounded gold-and-brown fan tail, two folded wings and two clawed feet.',
'Ghost':'Floating white cartoon ghost with two dark oval eyes, small oval mouth, short white side arm-like flaps and wavy tapered lower hem. Preserve white body; no bat wings or legs.',
'Goat':'White shaggy goat with ochre patches, two short dark banded horns, pointed ears, chin beard, four hooves and tiny upturned tail.',
'Gobbler':'Tall gold-brown turkey, spotted neck with golden feather crest, dark body, very broad gold striped fan tail, short wings and two clawed feet.',
'Goose':'Tall white goose with long neck, ochre cheek and body spots, broad golden bill, folded white wings, short tail, two orange webbed feet.',
'GreenParasite':'Despite the name, original is dark ochre-brown with huge ivory teeth, pale underside and large ivory conical dorsal spikes; tapering segmented legless slug.',
'GreenScorpion':'Original is golden-brown, not green: six walking legs, two pincers, thin ivory horns and a tall arched segmented tail with downward-hooked ivory sting. Back tail grows from the rear and rises above the body.',
'Hen':'Cream-white hen with ochre spots, golden comb, beak and wattle, cream wings, short upright white tail and two golden clawed feet.',
'Hog':'Very round golden-brown spotted boar, big ivory tusks, short horns/ears, four tiny hooves and small pointed tail.',
'Horse':'Golden-brown spotted horse with cream forelock, stern cream eyes, ochre mane and long ochre tail, a rectangular gold saddle pad with ivory border, four hooves. No rider.',
'Husky':'White-gray shaggy husky with brown ears and ochre patches, thick white facial mask, pointed ears, four paws and a bushy white-tipped tail.',
'IceParasite':'Original is olive-gold, not blue: huge ivory teeth, pale lower jaw, large translucent-looking amber crystal spikes along a tapering legless segmented body.',
'InfectedRat':'Dark olive shaggy rat with amber eye, torn fur, gold scars/patches, four short paws and thin pale ringed tail.',
'Juggernaut':'Gray muscular ogre with gold mohawk, spiked shoulder armor, diagonal yellow strap, dark broad belt and a heavy dark iron studded mace in his RIGHT hand.',
'Larva':'Plain legless golden-brown larva with low rounded segmented body, sleepy amber eye and zigzag mouth. No spikes or legs.',
'Lion':'Golden lion with large sweeping ochre mane, cream muzzle, visible fangs, four broad cream-clawed paws and long thin tufted tail.',
'LittleBunny':'Small pale-white rabbit with subtle gray and ochre spots, big upright ears, buck teeth, four tiny paws and a cotton tail.',
'Maneater':'Ochre-skinned stocky ogre with short dark hair, pointed ears and chin beard, gold leather armor and loincloth, squared belt buckle and wooden spiked club in his RIGHT hand.',
'MeatBug':'Low brown oval segmented bug with gold spots, stern amber eyes, six short gold feet, and two long golden curved forward antennae emerging near the face. No tail.',
'MechanicalParasiteTypeA':'Bright gold metallic legless segmented parasite, huge ivory teeth, large ivory conical back spikes, round slotted screw plates and gold mechanical armor.',
'MechanicalParasiteTypeB':'Dark olive metallic legless segmented parasite, huge ivory teeth, ivory conical back spikes, slotted round screws and plated golden underside.',
'Mimic':'Open golden wooden treasure chest monster, rounded lid, dark iron bands, huge ivory teeth along both jaws and long ochre spotted tongue. No legs; preserve box, hinged lid, teeth and tongue.',
'MimicChest':'Closed golden wooden chest with arched lid, two gray iron bands, central gray lock and visible plank grain. No eyes, limbs or teeth in normal state; broken/dead state follows original broken chest art.',
'MinerBoar':'Round very dark olive spotted boar with ivory tusks, ochre mining helmet and luminous pale headlamp, gray-brown harness, four tiny dark feet and small tail.',
'MohawkBat':'Dark charcoal bat, huge pointed ears, orange mohawk, cream eyes, fangs, tiny brown nose and large dark ribbed leathery wings. No tail.',
'Monkey':'Small golden monkey with enormous round cream ears, cream oval face and muzzle, white eyes, small crest, four short paws and long curled golden tail. Preserve its existing current direction work when valid.',
'MosquitoParasite':'Dark olive segmented legless parasite with a huge ivory tooth mouth, tiny bumpy dorsal projections and tapering rear. No mosquito wings in its original visible body.',
'MossQueen':'Low ochre insect queen, enormous furry ochre moss-covered round abdomen topped by several tan-and-cream mushrooms, tiny dark horned head and six short pale pointed armored legs. No wings.',
'MossQueenMounted':'Moss queen insect with fuzzy ochre round abdomen and a rectangular golden leather saddle ON TOP instead of the mushroom cluster; six short ivory-tipped legs, horned head. No rider.',
'Nightmare':'Large dark olive demon dog with gold mane, huge ivory forehead horn, small ivory dorsal spikes, four broad paws and long thin dark tail.',
'Ogre':'Olive-brown ogre with bald pate and short topknot, chain necklace, skull belt, gold leather loincloth, thick arms and wooden club in RIGHT hand.',
'Ox':'Golden spotted ox, small curved ochre horns, cream muzzle and big cream eyes, four hooves, thin tufted tail.',
'Panther':'Dark olive spotted panther with yellow eyes, round small ears, muscular low body, four paws and long smooth thin tail.',
'Pig':'Round golden-tan spotted pig, huge cream eyes, broad snout, triangular ears, four tiny feet and short thin tail. No tusks.',
'Piggy':'Pale cream piglet with ochre spots, huge cream eyes, short snout, four tiny feet and a curly tail. No tusks.',
'PirateBoar':'Round golden spotted boar, ivory tusks, brown pirate tricorn with skull emblem, hanging chain, and a huge barrel cannon with wooden support mounted on top. Four tiny feet; preserve cannon, hat and chain, no rider.',
'Pony':'Small golden spotted horse with dark ochre forelock and mane, cream muzzle, four hooves, long tail and a gold saddle pad edged with ivory. No rider.',
'Porcupine':'Low gray-brown porcupine with stern cream eye, small round ear, buck teeth, four small paws and a huge fan of long cream-and-dark-brown back quills. No invented long tail.',
'Porky':'Round pale tan pig with gray and ochre spots, huge cream eyes, small ivory tusks, four tiny feet and a curled tail.',
'PossessedBlackBear':'Very shaggy dark olive bear with amber glowing eyes, gold dorsal spikes and patches, heavy fangs, four thick clawed paws and short tail.',
'PossessedBlackBoar':'Round dark olive possessed boar with gold glowing eyes, long ivory tusks, gold dorsal spikes and scars, four tiny feet and short tail.',
'PossessedRat':'Dark olive rat with amber glowing eye, spiky gold-highlighted fur, long thin pale ringed tail and four short paws.',
'PossessedWarg':'Dark olive snarling warg with amber eyes, angular gold dorsal spikes, ragged fur, long bushy tail and four clawed paws.',
'PossessedWatchdog':'Dark olive bulky guard dog with amber eyes, large cream tusklike fangs, heavy ochre spiked collar, ragged gold spines, bushy tail and four broad paws.',
'PossessedWolf':'Dark olive lean wolf with amber eyes, sharp gold dorsal spikes, shaggy head and cheeks, long tail and four paws.',
'Pug':'Round golden pug with dark brown muzzle and floppy ears, huge white eyes, four tiny paws and tightly curled tail.',
'Punisher':'Olive-gray ogre wearing a full dark spotted helmet with a narrow gold eye slit, chain mail and spiked shoulder armor, holding a curved notched battle axe in RIGHT hand.',
'PurpleScarab':'Despite name, original is tan-and-cream spotted armored beetle with ivory glowing lens eyes, six long cream jointed legs and dark mandibles. Preserve actual tan palette.',
'Ram':'Dark gray-olive woolly ram with ochre patches, golden face, two massive curled cream horns, beard and four hooves, tiny tail integrated into wool.',
'Rat':'Low dark olive shaggy rat with amber eye, cream teeth, round ears, four small paws and long pale striped tail.',
'RatKing':'Large olive ragged rat with small gold crown, amber eye, pale cheek tufts, four paws and long thin striped tail. Preserve crown.',
'RedScorpion':'Original is golden yellow with ochre patches, six walking legs, two pincers, large ivory spikes and a high segmented arch tail with its stinger curling down. No red recolor.',
'Rooster':'Cream-white spotted rooster, long gold neck, golden comb and wattles, cream folded wings, short upright white tail, two golden clawed feet.',
'RoyalBoar':'Very round bright golden boar with cream swept forelock, big ivory tusks, ochre spots, four small feet and tiny pointed tail. No crown in its current original.',
'SabretoothTiger':'White saber-toothed tiger with dark brown stripes and ochre patches, huge long ivory canines, cheek ruff, four cream-clawed paws and striped tail.',
'Scarab':'Dark olive beetle with ochre patches, orange luminous lens eyes, ivory curved mandibles, plated oval back and six long cream jointed legs.',
'ScarabMounted':'Dark olive orange-eyed beetle with six long cream jointed legs, ivory mandibles and brown leather saddle on its back. No rider.',
'ShardLizard':'Small low dark olive lizard with ochre patches, angular square cream crystal shards across head and back, four splayed feet and long pointed segmented tail.',
'Sheep':'Cream-white fluffy sheep with ochre patches, cream face, big oval eyes and drooping ears, no horns, four tiny dark hooves, small woolly tail.',
'SlugQueen':'Legless brown segmented slug queen with ochre spots, small golden crown and short snout, stern gold eyes, large rounded arched back. Preserve crown, no legs.',
'Swine':'Round golden-tan spotted boar with ivory tusks, four short feet and tiny tapered tail.',
'Tiger':'Gold tiger with dark stripes and ochre spots, cream cheek ruff, forehead curl, cream muzzle, four big clawed paws and long striped tail.',
'TreasureChest':'Closed golden wooden chest with rounded lid, gray iron bands and square lock, black plank outlines; no face, legs or tongue in normal state.',
'Troll':'Golden ochre bald troll with pointed ears, small fang mouth, leather belt and loincloth, tooth necklace, thick short legs and stone-headed hammer in RIGHT hand.',
'Turkey':'Golden tan spotted turkey with cream neck, long gold wattle and huge cream-and-ochre fan tail, two folded wings and two clawed feet.',
'VolcanoParasite':'Golden brown legless segmented parasite, enormous ivory tooth mouth, pale lower jaw and curved dark volcanic-looking spikes on its back.',
'Warg':'Dark olive shaggy warg with amber eyes, pointed ears, gold spots, long tail and four clawed paws.',
'Wasp':'Flying golden ochre wasp with black-brown abdomen bands, two long antennae, round eye plates, translucent cream veined wings, small dangling claws and pointed sting.',
'Watchdog':'Dark olive guard dog with ivory jaw fangs, heavy golden collar with ivory spikes, pointed ears, four broad paws and short upright pointed tail.',
'WhiteWolf':'White shaggy wolf with ochre patches, golden eyes, pointed ears, long white bushy tail and four cream-clawed paws.',
'WildGoat':'Gray-tan spotted goat with long swept curved horns, cream beard and belly, four hooves and small raised pale tail.',
'WildRooster':'Golden rooster with tall orange-gold comb, cream face and neck ring, angular beak, gold folded wings and upright tail, two clawed feet.',
'WinterBear':'White shaggy bear with dark brown stripes and ochre patches, stern white eyes, broad golden muzzle, four heavy clawed paws and short fur tail.',
'WinterBoar':'Round white shaggy boar with ochre patches, dark swept mane, huge ivory tusks, golden snout, four tiny paws and small tail.',
'WinterOgre':'Stocky golden ogre with bald head, pointed ears, cream fur loincloth and boots, huge fur-rimmed spiked wrist guards, open empty fists; original has NO handheld weapon.',
'WinterWarg':'White shaggy warg with dark brown dorsal spines, amber eyes, long white tail and four clawed paws.',
'WinterWolfTypeA':'Brown-and-white shaggy wolf, brown upper back and ears, white face/chest/legs/tail tip, amber eyes, four paws.',
'WinterWolfTypeB':'White shaggy wolf with ochre patches, dark banded pointed ears, amber eyes, four paws and long white tail.',
'Wolf':'Dark gray-brown shaggy wolf with ochre patches, cream eyes, pointed ears, four paws and long bushy tail.',
'WolfHound':'Lean dark olive hound with ochre face, gold collar, large pointed ears, fangs, four paws and long swept-up bushy tail.',
'WolfMounfed':'Dark gray-olive wolf wearing the original gold leather saddle and gray girth buckle, cream eyes, long bushy tail and four paws. Name spelling is intentional; NO rider.',
'Zombie':'Olive-gray stitched ogre zombie with exposed cream brain, pale round eyes, skull and bone trinkets, leather loincloth, thick metal wrist guard and wooden spiked club in RIGHT hand.'
}
if name not in identities: raise ValueError('Missing individual identity description: '+name)
if family in ['BugQueen','Scarab','Caterpillar','MeatBug']: kind='hexapod'
elif family=='Scorpion': kind='scorpion'
elif family=='Giant': kind='giant'
elif family in ['Rooster','Chicken','Duck','Turkey']: kind='bird'
elif family in ['Larva','Parasite']: kind='crawler'
elif family in ['Container','Mimic']: kind='chest'
elif name in ['FlyingDemon','Ghost']: kind='floating'
elif family in ['Bat','Wasp']: kind='flying'
else: kind='quadruped'
parts={
'quadruped':['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack','Tail'],
'hexapod':['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegMiddle','LegBack','Feelers'],
'scorpion':['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegMiddle','LegBack','Claw','Tail'],
'giant':['HeadNormal','HeadAngry','HeadDead','Body','ArmWeapon','ArmFree','Leg'],
'bird':['HeadNormal','HeadAngry','HeadDead','Body','Wing','Leg','Tail'],
'crawler':['HeadNormal','HeadAngry','HeadDead','Body','Segment','Tip'],
'chest':['HeadNormal','HeadAngry','HeadDead','Body','Tongue'],
'floating':['HeadNormal','HeadAngry','HeadDead','Body','Flap'],
'flying':['HeadNormal','HeadAngry','HeadDead','Body','WingRaised','WingLowered']
}[kind]
# Do not invent feelers for queens/beetles, or tongues for ordinary containers.
if kind=='hexapod' and name!='MeatBug': parts=parts[:-1]
if kind=='floating' and name!='Ghost': parts=parts[:-1]
if kind=='chest' and family!='Mimic': parts=parts[:-1]
cols,rows=(3,3) if kind=='scorpion' else (4,2)
descriptions={
'HeadNormal':'detached normal head only, including its original ears/horns/crest/hat, NO torso',
'HeadAngry':'same head and alignment, angry attack expression',
'HeadDead':'same head and alignment, dead expression',
'Body':'detached complete torso/back and rump ONLY, preserving original dorsal details/saddle/armor, NO head, legs, tail or wings',
'LegFront':'ONE left foreleg, with rounded shoulder root at TOP RIGHT, toes aimed along travel direction',
'LegMiddle':'ONE left middle walking leg with rounded root at TOP RIGHT, bent outward and downward LEFT',
'LegBack':'ONE left hindleg, rounded hip root at TOP RIGHT, bent outward and downward LEFT',
'Tail':'ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type',
'Claw':'ONE LEFT pincer arm with both jaws, shoulder/root at RIGHT, jaws extending LEFT and forward',
'Feelers':'ONE left curved forward feeler, root at RIGHT, extending outward LEFT',
'ArmWeapon':'ONE complete anatomical RIGHT arm, shoulder at TOP center; INCLUDE original right-hand weapon held naturally, no second arm or torso',
'ArmFree':'ONE complete anatomical LEFT arm including its glove/guard if original, shoulder at TOP center; no weapon or torso',
'Leg':'ONE left leg/foot, root at TOP center, toes down towards the ground',
'Wing':'ONE left folded feather wing, shoulder at TOP RIGHT; fan of feathers extends LEFT/DOWN',
'WingRaised':'ONE left wing fully raised, shoulder attachment at RIGHT edge; wing fans LEFT',
'WingLowered':'same left wing spread/lowered, same shoulder and anatomy',
'Segment':'ONE detached middle body segment, matching rounded back and pale belly',
'Tip':'ONE detached rear tip/rump, corresponding to the actual back of this creature',
'Tongue':'ONE original ochre tongue, connection root at TOP center, tip pointing DOWN',
'Flap':'ONE short white side arm-like flap, root at RIGHT edge, extending LEFT, no fingers'
}
if kind=='scorpion': descriptions['Tail']='ONE complete upright segmented tail, root at BOTTOM center, rises straight UP then arches OVER near center, ivory stinger hooks DOWN beyond arch; a high rear-view arch, NOT a low inward spiral or diagonal sideways reach'
if kind=='quadruped':
    descriptions['LegFront']='ONE detached left foreleg with rounded shoulder root at TOP CENTER, front-facing hoof/paw at bottom; show the view-appropriate front/back of foot, no side-profile toes'
    descriptions['LegBack']='ONE detached left hindleg with rounded hip root at TOP CENTER and view-appropriate hoof/paw at bottom; no extra leg'
if kind=='hexapod':
    descriptions['LegFront']='ONE left front jointed insect walking leg, root at TOP RIGHT, extends outward LEFT then down; no extra legs'
    descriptions['LegBack']='ONE left rear jointed insect walking leg, root at TOP RIGHT, extends outward LEFT then down; distinct from front leg'
if kind=='chest':
    descriptions['HeadNormal']='the complete original upper chest/lid ONLY with normal original expression/state, hinge at BOTTOM center; no box base'
    descriptions['HeadAngry']='same upper chest/lid in original attack/open state, same dimensions; preserve normal chest identity'
    descriptions['HeadDead']='same upper chest/lid with original broken/dead appearance, same alignment'
    descriptions['Body']='the chest BOX BASE only, original wood grain, lock/bands/teeth where original; no upper lid or tongue'
if kind=='floating':
    descriptions['HeadNormal']='the original upper body/head with its complete front face, or its plain corresponding back when rear-facing; no lower hem'
    descriptions['Body']='the matching lower body cap or tapered lower ghost hem ONLY, rounded connection at top; no duplicate face'
if kind=='crawler':
    descriptions['Body']='complete central/back body section, original dorsal details and belly; no head or rear tip'
if name=='Cerberus':
    for p in ['HeadNormal','HeadAngry','HeadDead']: descriptions[p]+='; THREE original canine heads together as ONE connected head-group slice, with three neck roots, not one head'
if name=='WinterOgre': descriptions['ArmWeapon']=descriptions['ArmWeapon'].replace('INCLUDE original right-hand weapon held naturally','EMPTY fist and original fur-rimmed spiked wrist guard; NO handheld weapon')
plan={'name':name,'kind':kind,'controller_family':family,'identity':identities[name],'parts':parts,'columns':cols,'rows':rows,'source':t['source'],'atlas':t['atlas'],'art_dir':t['art_dir'],'controller':t['controller']}
directory=HERE/name
(directory/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    rear=direction=='Up'
    view='REAR/BACK view, travelling AWAY toward screen UP. NO visible eyes, nostrils, teeth, inner-ear pads or face on the back of the head. Only plain outer backs of ears, actual original rear head hair/hat, rump and tail are visible.' if rear else 'FRONT view travelling TOWARD viewer, screen DOWN. Show the matching face and forward-pointing feet, with correct forehead/neck and chest connections.'
    view_descriptions=dict(descriptions)
    if kind=='quadruped':
        view_descriptions['Body']+='; AXIAL elevated quadruped view: '+('neck at TOP center and broad rump at BOTTOM' if rear else 'broad far rump at TOP and narrow near neck/chest at BOTTOM center, so head overlaps neck BELOW torso; NOT upright human torso')+'; all four limbs detached, no painted feet'
        view_descriptions['Tail']='ONE full detached original tail, ROOT at TOP CENTER, hanging DOWN with the original curve and tuft; preserve actual tail type' if family=='Cow' else descriptions['Tail']
    slots='\n'.join(str(i+1)+'. '+view_descriptions[p]+(' (rear view: expressions use the SAME plain rear head silhouette, no face)' if rear and p.startswith('Head') else '') for i,p in enumerate(parts))
    prompt=f'''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet.
Image 1 is the CURRENT ORIGINAL sprite atlas. Image 2 is the complete CURRENT ORIGINAL character rendered from its serialized prefab, reference only. These determine color, identity, anatomy, equipment, outline and proportions.
Character {name}: {identities[name]}
Requested view: {view} Same elevated orthographic game perspective as source, never rotate/flip/stretch its side sprite to fake a new view.
One sheet, exactly {cols} equal columns by {rows} equal rows, cells in reading order:
{slots}
Remaining cells must be empty. Each part centered within its own cell, 12 percent empty padding; no labels, grid lines or cell-crossing parts. No complete assembled creature. Detached parts must have solid opaque rounded connection roots and match when layered. All three head states same size and alignment. Torso includes all distinctive back adornment visible from this view (mushrooms, crystals, mane, saddle, armor, cannon or fan feathers where present), but excludes anything assigned its own cell. Tail, when present, must match the actual original tail and attach at its rear root.
Style: exact original warm gold/olive/cream palette, thick smooth dark outline, broad simple cartoon cel shaded color regions. Preserve reference-specific features; filenames are NOT color instructions. Straight-on axial front or rear composition; muzzle centered below eyes, never three-quarter or looking left/right. No invented dorsal manes, hair stripes, knobs, horns, organs or equipment absent from original. Neck and limb connection roots must be SOLID opaque shapes, NEVER hollow tubes or open holes. Ground contact and limb orientation must be plausible for this view.
Background exactly flat RGB #FF00FF magenta immediately outside each outline. All part interiors opaque source colors; no magenta holes. NO floor, NO ground shadow, NO cast shadow, NO soft glow, NO blurry halo, NO vignette, no checkerboard, no text, no watermark. Crisp intact outlines suitable for removing magenta to true transparency.
'''
    out=directory/'generation'/direction;out.mkdir(parents=True,exist_ok=True)
    if (out/'request.json').exists(): raise ValueError('Request already exists; do not overwrite prompt or repeat a paid request')
    (out/'prompt.txt').write_text(prompt,encoding='utf-8')
print(json.dumps({'name':name,'kind':kind,'parts':parts},ensure_ascii=False))
