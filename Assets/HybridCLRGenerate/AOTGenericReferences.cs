using System.Collections.Generic;
public class AOTGenericReferences : UnityEngine.MonoBehaviour
{

	// {{ AOT assemblies
	public static readonly IReadOnlyList<string> PatchedAOTAssemblyList = new List<string>
	{
		"System.Core.dll",
		"UnityEngine.AssetBundleModule.dll",
		"UnityEngine.CoreModule.dll",
		"UnityEngine.JSONSerializeModule.dll",
		"YooAsset.dll",
		"mscorlib.dll",
	};
	// }}

	// {{ constraint implement type
	// }} 

	// {{ AOT generic types
	// System.Action<FTProject.WaveManager.SpawnEntry>
	// System.Action<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Action<UnityEngine.Vector2>
	// System.Action<YooAsset.DownloadErrorEventArgs>
	// System.Action<YooAsset.DownloadProgressChangedEventArgs>
	// System.Action<byte,object>
	// System.Action<byte>
	// System.Action<float>
	// System.Action<int,int,int>
	// System.Action<int,int,long,long>
	// System.Action<int,int>
	// System.Action<int>
	// System.Action<long,long>
	// System.Action<object,float>
	// System.Action<object,int>
	// System.Action<object,object,object,object>
	// System.Action<object,object,object>
	// System.Action<object,object>
	// System.Action<object>
	// System.Collections.Generic.ArraySortHelper<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.ArraySortHelper<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.ArraySortHelper<UnityEngine.Vector2>
	// System.Collections.Generic.ArraySortHelper<byte>
	// System.Collections.Generic.ArraySortHelper<float>
	// System.Collections.Generic.ArraySortHelper<int>
	// System.Collections.Generic.ArraySortHelper<object>
	// System.Collections.Generic.Comparer<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.Comparer<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.Comparer<UnityEngine.Vector2>
	// System.Collections.Generic.Comparer<byte>
	// System.Collections.Generic.Comparer<float>
	// System.Collections.Generic.Comparer<int>
	// System.Collections.Generic.Comparer<object>
	// System.Collections.Generic.Dictionary.Enumerator<int,object>
	// System.Collections.Generic.Dictionary.Enumerator<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary.Enumerator<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary.Enumerator<object,int>
	// System.Collections.Generic.Dictionary.Enumerator<object,object>
	// System.Collections.Generic.Dictionary.KeyCollection.Enumerator<int,object>
	// System.Collections.Generic.Dictionary.KeyCollection.Enumerator<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary.KeyCollection.Enumerator<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary.KeyCollection.Enumerator<object,int>
	// System.Collections.Generic.Dictionary.KeyCollection.Enumerator<object,object>
	// System.Collections.Generic.Dictionary.KeyCollection<int,object>
	// System.Collections.Generic.Dictionary.KeyCollection<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary.KeyCollection<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary.KeyCollection<object,int>
	// System.Collections.Generic.Dictionary.KeyCollection<object,object>
	// System.Collections.Generic.Dictionary.ValueCollection.Enumerator<int,object>
	// System.Collections.Generic.Dictionary.ValueCollection.Enumerator<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary.ValueCollection.Enumerator<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary.ValueCollection.Enumerator<object,int>
	// System.Collections.Generic.Dictionary.ValueCollection.Enumerator<object,object>
	// System.Collections.Generic.Dictionary.ValueCollection<int,object>
	// System.Collections.Generic.Dictionary.ValueCollection<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary.ValueCollection<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary.ValueCollection<object,int>
	// System.Collections.Generic.Dictionary.ValueCollection<object,object>
	// System.Collections.Generic.Dictionary<int,object>
	// System.Collections.Generic.Dictionary<object,FTProject.LocEntry>
	// System.Collections.Generic.Dictionary<object,FTProject.ResAddress>
	// System.Collections.Generic.Dictionary<object,int>
	// System.Collections.Generic.Dictionary<object,object>
	// System.Collections.Generic.EqualityComparer<FTProject.LocEntry>
	// System.Collections.Generic.EqualityComparer<FTProject.ResAddress>
	// System.Collections.Generic.EqualityComparer<int>
	// System.Collections.Generic.EqualityComparer<object>
	// System.Collections.Generic.HashSet.Enumerator<int>
	// System.Collections.Generic.HashSet.Enumerator<object>
	// System.Collections.Generic.HashSet<int>
	// System.Collections.Generic.HashSet<object>
	// System.Collections.Generic.HashSetEqualityComparer<int>
	// System.Collections.Generic.HashSetEqualityComparer<object>
	// System.Collections.Generic.ICollection<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.ICollection<System.Collections.Generic.KeyValuePair<int,object>>
	// System.Collections.Generic.ICollection<System.Collections.Generic.KeyValuePair<object,FTProject.LocEntry>>
	// System.Collections.Generic.ICollection<System.Collections.Generic.KeyValuePair<object,FTProject.ResAddress>>
	// System.Collections.Generic.ICollection<System.Collections.Generic.KeyValuePair<object,int>>
	// System.Collections.Generic.ICollection<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.ICollection<UnityEngine.Vector2>
	// System.Collections.Generic.ICollection<byte>
	// System.Collections.Generic.ICollection<float>
	// System.Collections.Generic.ICollection<int>
	// System.Collections.Generic.ICollection<object>
	// System.Collections.Generic.IComparer<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.IComparer<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.IComparer<UnityEngine.Vector2>
	// System.Collections.Generic.IComparer<byte>
	// System.Collections.Generic.IComparer<float>
	// System.Collections.Generic.IComparer<int>
	// System.Collections.Generic.IComparer<object>
	// System.Collections.Generic.IEnumerable<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<int,object>>
	// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,FTProject.LocEntry>>
	// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,FTProject.ResAddress>>
	// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,int>>
	// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.IEnumerable<UnityEngine.Vector2>
	// System.Collections.Generic.IEnumerable<byte>
	// System.Collections.Generic.IEnumerable<float>
	// System.Collections.Generic.IEnumerable<int>
	// System.Collections.Generic.IEnumerable<object>
	// System.Collections.Generic.IEnumerator<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.IEnumerator<System.Collections.Generic.KeyValuePair<int,object>>
	// System.Collections.Generic.IEnumerator<System.Collections.Generic.KeyValuePair<object,FTProject.LocEntry>>
	// System.Collections.Generic.IEnumerator<System.Collections.Generic.KeyValuePair<object,FTProject.ResAddress>>
	// System.Collections.Generic.IEnumerator<System.Collections.Generic.KeyValuePair<object,int>>
	// System.Collections.Generic.IEnumerator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.IEnumerator<UnityEngine.Vector2>
	// System.Collections.Generic.IEnumerator<byte>
	// System.Collections.Generic.IEnumerator<float>
	// System.Collections.Generic.IEnumerator<int>
	// System.Collections.Generic.IEnumerator<object>
	// System.Collections.Generic.IEqualityComparer<int>
	// System.Collections.Generic.IEqualityComparer<object>
	// System.Collections.Generic.IList<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.IList<System.Collections.Generic.KeyValuePair<int,object>>
	// System.Collections.Generic.IList<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.IList<UnityEngine.Vector2>
	// System.Collections.Generic.IList<byte>
	// System.Collections.Generic.IList<float>
	// System.Collections.Generic.IList<int>
	// System.Collections.Generic.IList<object>
	// System.Collections.Generic.KeyValuePair<int,object>
	// System.Collections.Generic.KeyValuePair<object,FTProject.LocEntry>
	// System.Collections.Generic.KeyValuePair<object,FTProject.ResAddress>
	// System.Collections.Generic.KeyValuePair<object,int>
	// System.Collections.Generic.KeyValuePair<object,object>
	// System.Collections.Generic.List.Enumerator<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.List.Enumerator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.List.Enumerator<UnityEngine.Vector2>
	// System.Collections.Generic.List.Enumerator<byte>
	// System.Collections.Generic.List.Enumerator<float>
	// System.Collections.Generic.List.Enumerator<int>
	// System.Collections.Generic.List.Enumerator<object>
	// System.Collections.Generic.List<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.List<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.List<UnityEngine.Vector2>
	// System.Collections.Generic.List<byte>
	// System.Collections.Generic.List<float>
	// System.Collections.Generic.List<int>
	// System.Collections.Generic.List<object>
	// System.Collections.Generic.ObjectComparer<FTProject.WaveManager.SpawnEntry>
	// System.Collections.Generic.ObjectComparer<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.Generic.ObjectComparer<UnityEngine.Vector2>
	// System.Collections.Generic.ObjectComparer<byte>
	// System.Collections.Generic.ObjectComparer<float>
	// System.Collections.Generic.ObjectComparer<int>
	// System.Collections.Generic.ObjectComparer<object>
	// System.Collections.Generic.ObjectEqualityComparer<FTProject.LocEntry>
	// System.Collections.Generic.ObjectEqualityComparer<FTProject.ResAddress>
	// System.Collections.Generic.ObjectEqualityComparer<int>
	// System.Collections.Generic.ObjectEqualityComparer<object>
	// System.Collections.Generic.Queue.Enumerator<object>
	// System.Collections.Generic.Queue<object>
	// System.Collections.Generic.Stack.Enumerator<object>
	// System.Collections.Generic.Stack<object>
	// System.Collections.ObjectModel.ReadOnlyCollection<FTProject.WaveManager.SpawnEntry>
	// System.Collections.ObjectModel.ReadOnlyCollection<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Collections.ObjectModel.ReadOnlyCollection<UnityEngine.Vector2>
	// System.Collections.ObjectModel.ReadOnlyCollection<byte>
	// System.Collections.ObjectModel.ReadOnlyCollection<float>
	// System.Collections.ObjectModel.ReadOnlyCollection<int>
	// System.Collections.ObjectModel.ReadOnlyCollection<object>
	// System.Comparison<FTProject.WaveManager.SpawnEntry>
	// System.Comparison<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Comparison<UnityEngine.Vector2>
	// System.Comparison<byte>
	// System.Comparison<float>
	// System.Comparison<int>
	// System.Comparison<object>
	// System.Func<System.Collections.Generic.KeyValuePair<object,object>,byte>
	// System.Func<object,int,int,object>
	// System.Func<object,int,object>
	// System.Func<object,object>
	// System.Func<object>
	// System.IEquatable<object>
	// System.Linq.Enumerable.Iterator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Linq.Enumerable.WhereArrayIterator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Linq.Enumerable.WhereEnumerableIterator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Linq.Enumerable.WhereListIterator<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Nullable<byte>
	// System.Nullable<double>
	// System.Nullable<float>
	// System.Nullable<int>
	// System.Nullable<long>
	// System.Nullable<short>
	// System.Predicate<FTProject.WaveManager.SpawnEntry>
	// System.Predicate<System.Collections.Generic.KeyValuePair<object,object>>
	// System.Predicate<UnityEngine.Vector2>
	// System.Predicate<byte>
	// System.Predicate<float>
	// System.Predicate<int>
	// System.Predicate<object>
	// UnityEngine.Events.InvokableCall<float>
	// UnityEngine.Events.UnityAction<UnityEngine.SceneManagement.Scene,int>
	// UnityEngine.Events.UnityAction<float>
	// UnityEngine.Events.UnityEvent<float>
	// }}

	public void RefMethods()
	{
		// object System.Activator.CreateInstance<object>()
		// byte[] System.Array.Empty<byte>()
		// object[] System.Array.Empty<object>()
		// System.Void System.Array.Sort<float>(float[],int,int)
		// System.Void System.Array.Sort<float>(float[],int,int,System.Collections.Generic.IComparer<float>)
		// System.Collections.Generic.KeyValuePair<int,object> System.Linq.Enumerable.ElementAt<System.Collections.Generic.KeyValuePair<int,object>>(System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<int,object>>,int)
		// System.Collections.Generic.KeyValuePair<object,object> System.Linq.Enumerable.ElementAt<System.Collections.Generic.KeyValuePair<object,object>>(System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,object>>,int)
		// System.Collections.Generic.KeyValuePair<object,object> System.Linq.Enumerable.First<System.Collections.Generic.KeyValuePair<object,object>>(System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,object>>)
		// System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,object>> System.Linq.Enumerable.Where<System.Collections.Generic.KeyValuePair<object,object>>(System.Collections.Generic.IEnumerable<System.Collections.Generic.KeyValuePair<object,object>>,System.Func<System.Collections.Generic.KeyValuePair<object,object>,bool>)
		// object& System.Runtime.CompilerServices.Unsafe.As<object,object>(object&)
		// System.Void* System.Runtime.CompilerServices.Unsafe.AsPointer<object>(object&)
		// object UnityEngine.AssetBundle.LoadAsset<object>(string)
		// object UnityEngine.Component.GetComponent<object>()
		// object UnityEngine.Component.GetComponentInChildren<object>(bool)
		// object UnityEngine.Component.GetComponentInParent<object>()
		// object[] UnityEngine.Component.GetComponentsInChildren<object>(bool)
		// object UnityEngine.GameObject.AddComponent<object>()
		// object UnityEngine.GameObject.GetComponent<object>()
		// object[] UnityEngine.GameObject.GetComponents<object>()
		// object[] UnityEngine.GameObject.GetComponentsInChildren<object>(bool)
		// object UnityEngine.JsonUtility.FromJson<object>(string)
		// object UnityEngine.Object.FindObjectOfType<object>()
		// object UnityEngine.Object.Instantiate<object>(object)
		// object UnityEngine.Object.Instantiate<object>(object,UnityEngine.Transform,bool)
		// object UnityEngine.Object.Instantiate<object>(object,UnityEngine.Vector3,UnityEngine.Quaternion,UnityEngine.Transform)
		// object UnityEngine.Resources.Load<object>(string)
		// object YooAsset.AssetHandle.GetAssetObject<object>()
		// string string.Join<int>(string,System.Collections.Generic.IEnumerable<int>)
		// string string.Join<object>(string,System.Collections.Generic.IEnumerable<object>)
		// string string.JoinCore<int>(System.Char*,int,System.Collections.Generic.IEnumerable<int>)
		// string string.JoinCore<object>(System.Char*,int,System.Collections.Generic.IEnumerable<object>)
	}
}